# Validation protocol and evidence

## Local checks already passed

`tests/test_hscc2027.py` contains 16 focused checks and passed with Python 3.13.14. It covers the single-M2-action quantifier, both fixed-vertex sides, absorbing probability, rejection of incomplete vertex enumeration, LP agreement with a two-point total-variation calculation, full label-matching initialization, multi-round relation refinement, bisection, Algorithm 2 invalid-input rejection, Algorithm 3 agreement with exhaustive relation search on a small model, progress events, and cached versus uncached bisection equivalence.

The handoff runner's optional `smoke` mode was run locally with two independent processes. Both semantics completed Algorithms 1, 2 and 3 on 1D (5,10). The run verified command expansion, stage dependencies, automatic cross-checks, isolated output directories and logging. The generated `runs/` directory is ignored by Git; it is not the archived local snapshot.

## Validation ladder for each server case

1. Confirm clean checkout and intended commit; run `python -m unittest tests.test_hscc2027 -q`.
2. Run one case and semantics with Algorithm 1. Confirm M1/M2 partition counts and total counts, both initial-state IDs, initial pair in `relation.csv`, row count, and bisection bracket width at most `1e-3`.
3. Read `history.json`: the upper probe must be feasible and the lower probe infeasible unless zero error is already feasible. Retain all logs.
4. Run Algorithm 2 on **that** relation. Its `epsilon_star` must lie in Algorithm 1's bracket; `pair_errors.csv` must have one data row per relation pair.
5. When practical, run Algorithm 3. Its `epsilon_min` should lie in the Algorithm 1 bracket. Cross-check the relation at Algorithm 3's exact error with an Algorithm 1 fixed-threshold run. The relation at a larger bisection upper bound need not be identical.
6. Compare with the local snapshot only after checking commit, seed, dependency versions and model direction. The older manuscript Table 1 is not a correctness oracle for this implementation.

The wrapper checks metadata, commit, state counts, initial-pair presence, CSV row count, bracket width and Algorithm 2/3 error-in-bracket when a same-commit Algorithm 1 result exists. These automated checks supplement review of anomalies.

## Debugging sequence

Start with `runs/<case>/<semantics>/<stage>/run.log`, then inspect `runs/batch_manifest.json` and `runs/summary.csv`. A missing Algorithm 2 relation means the matching Algorithm 1 task has not completed under the same `--out-root`. A Git mismatch means outputs from different revisions were mixed; use distinct output roots or rerun at a fixed commit. A support-limit error must be reported, not bypassed with partial vertices. For a suspected cache issue, rerun Algorithm 1 directly with `--no-action-cache` and compare brackets and relation CSVs.

Do not change mathematical quantifiers, relation initialization or manuscript numbers to work around a failed job. Identify the model, solver or resource cause first.
