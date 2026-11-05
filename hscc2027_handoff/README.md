# HSCC 2027 experiment handoff

This is Weijie's entry point for Ouldouz to **inspect the current implementation, review local evidence, and run each server experiment separately**. M1 is the smaller abstract model; M2 is the larger concrete model. Cooperative and competitive semantics use the revised manuscript quantifiers. The solver entry point is `run_hscc2027.py`; `hscc2027_handoff/run_experiments.py` runs one specified experiment with a dedicated log and basic result checks.

## Start here after pulling

Run these commands from the repository root on a clean, fixed revision:

```bash
git fetch origin hscc2027-algorithm1
git switch hscc2027-algorithm1
git rev-parse HEAD
git status -sb
python hscc2027_handoff/run_experiments.py --suite status
python -m unittest tests.test_hscc2027 -q
```

The status command reports commit, working-tree state, Python/NumPy/SciPy/JAX versions, CPU count and output location. The 16 focused tests must pass. Use a Python 3.13 environment with the benchmark dependencies. The repository `requirements.txt` does not list JAX; verify `import jax` separately if preparing a new environment.

**[EXPERIMENT_COMMANDS.md](EXPERIMENT_COMMANDS.md) is the per-experiment command list.** It contains 60 commands: 10 Table 1 cases × 2 semantics × 3 algorithms. Each command specifies **one case, one semantics, and one algorithm**. For example, this runs only Algorithm 1 for cooperative 1D (5,10):

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_10 --semantics cooperative --jobs 1
```

Run the matching Algorithm 1 command before Algorithm 2, because Algorithm 2 reads its fixed relation CSV. Algorithm 3 can run independently, but check its cost on small cases first. [SERVER_RUNBOOK.md](SERVER_RUNBOOK.md) explains the order, optional parallel jobs, result checks and debugging. A CSV version of all commands is [experiment_commands.csv](experiment_commands.csv).

## Where to inspect Weijie's evidence

- [Local result archive](local_results/README.md): 27 original run directories, per-run result index, equivalent reproduction commands and SHA-256 file manifest.
- [Experiment log](records/EXPERIMENT_LOG.md): exact local results, provenance, comparisons and limitations.
- [Algorithm alignment](records/ALGORITHM_ALIGNMENT.md): manuscript quantifiers, M1/M2 direction and code mapping.
- [Validation protocol](records/VALIDATION_PROTOCOL.md): tests, acceptance criteria and debugging steps.
- [Progress and CPU performance](records/PERFORMANCE_AND_PARALLELISM.md): cached/uncached comparisons and the 64-core CPU parallelism boundary.
- [Single-task runner reference](../HSCC_2027_RUN.md): direct runner arguments and output fields.

| Locally checked M1/M2 partition sizes | Cooperative Algorithm 1 bracket | Competitive Algorithm 1 bracket | Algorithm 3 |
| --- | --- | --- | --- |
| 5/10 | [0.499023, 0.500000] | [0, 0.000977] | Both semantics checked |
| 5/15 | [0.951172, 0.952148] | [0, 0.000977] | Both semantics checked |
| 7/21 | [0.507813, 0.508789] | [0, 0.000977] | Not yet run locally |

These are **local validation outputs, not submitted Table 1 results**. The older table came from the earlier implementation. Its first three competitive upper bounds happen to match after rounding, while relation sizes and LP counts differ; the old table is not a correctness oracle for the revised code. Ouldouz's clean-checkout server results are still required.

## Outputs and optional concurrency

A single command writes to `hscc2027_handoff/runs/<case>/<semantics>/<stage>/` by default. This directory is ignored by Git. Each task has `run.log`, `result.json`, `history.json`, `relation.csv`, and Algorithm 2 also has `pair_errors.csv`. `runs/summary.csv` accumulates all task results across invocations; `runs/batch_manifest.json` describes the latest invocation. Logs flush probe, round, pair and LP progress; use `tail -f` on the relevant `run.log`.

Use the same `--out-root /scratch/HSCC_2027_runs` on every command if writing to a server work disk. `--dry-run` prints the expanded command, and `--force` reruns a validated clean-checkout result. Independent single-experiment commands may run simultaneously in separate terminals. Optional grouped scheduling with `--jobs 2` is documented in the runbook; it is **not** the primary workflow. The current implementation does not parallelize state-pair checks within one experiment.

## Paper update gate

Check server commit, environment, model sizes, initial pair, brackets, relation row counts and Algorithm 2/3 cross-checks before updating the manuscript. Any draft changes must be highlighted with color for Sadegh's review. This directory does not send email.
