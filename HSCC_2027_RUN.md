# HSCC 2027: revised Algorithm 1 baseline

`run_hscc2027.py` is the single entry point for revised Algorithms 1, 2, and
3 experiments.
It treats **M1 as the smaller abstract IMDP** and **M2 as the larger concrete
IMDP**, includes the separately stored absorbing probability, and initializes
the relation with every label-matching state pair. It uses complete vertex
enumeration and SciPy/HiGHS coupling LPs. The historical `run_experiment.py`,
`compare_methods*.py`, and `steps/step2_epsilon_search.py` implement earlier
definitions and must not be used for the revised table.

## Local validation completed

The ten checks in `tests/test_hscc2027.py` pass. The 1D pair `(5,10)` was run
under both semantics at fixed epsilon and with bisection tolerance `1e-3`.
These runs verified the pipeline and output schema; they are not the submitted
Table 1 measurements.

## Environment and invocation

Use Python 3.13 with NumPy, SciPy, JAX, and the benchmark dependencies.
From the repository root:

```bash
python -m unittest tests.test_hscc2027 -q
python run_hscc2027.py --model 1D --coarse 5 --fine 10 \
  --semantics cooperative --eps-tol 1e-3 --out-dir runs_hscc2027/1D_5_10_cooperative
python run_hscc2027.py --model 1D --coarse 5 --fine 10 \
  --semantics competitive --eps-tol 1e-3 --out-dir runs_hscc2027/1D_5_10_competitive
```

For fixed-epsilon diagnosis, add `--epsilon 0.1 --diagnose`. The output contains
`result.json` (model direction, state counts, error bracket, LP count, commit),
`history.json` (all bisection probes), and `relation.csv` (M1/M2 state pairs).
`diagnostic.json` is added in fixed-epsilon diagnostic mode. Timing excludes
benchmark model construction and includes relation computation across probes.

## Algorithm 2: minimum error for a fixed relation

Supply an existing `relation.csv` with exactly `M1_state,M2_state` columns.
The relation must contain the initial pair, use valid state IDs, and preserve
labels. The command evaluates the relation unchanged under the requested
semantics; it does not search for another relation. For example, after the
cooperative Algorithm 1 command above:

```bash
python run_hscc2027.py --model 1D --coarse 5 --fine 10 \
  --semantics cooperative \
  --relation-csv runs_hscc2027/1D_5_10_cooperative/relation.csv \
  --out-dir runs_hscc2027/1D_5_10_cooperative_fixed_relation
```

Run the corresponding competitive command with its own Algorithm 1 relation.
Algorithm 2 writes `result.json` with `epsilon_star` and `worst_pair`, plus
`pair_errors.csv`, `relation.csv`, and an empty `history.json`. An Algorithm 1
relation at a feasible bisection upper bound may have a smaller exact fixed
relation error; compare `epsilon_star` with the bisection bracket. State the
source of the chosen fixed relation when reporting Algorithm 2 results.

## Algorithm 3: joint minimum error and greatest relation

Use `--joint` with the same model and semantics options, without `--epsilon`
or `--relation-csv`:

```bash
python run_hscc2027.py --model 1D --coarse 5 --fine 10 \
  --semantics cooperative --joint \
  --out-dir runs_hscc2027/1D_5_10_cooperative_joint
```

Repeat for `competitive`. The output `result.json` contains `epsilon_min`,
the best relation size, LP count, and elimination rounds. `relation.csv` is
the greatest relation at that error, and `history.json` records every
removed pair, current error, improvement, and LP count. Compare the exact
`epsilon_min` with Algorithm 1's bisection bracket, and compare relations
when the bisection upper bound is close enough. Algorithm 3 currently
recomputes every local error after each deletion, so begin with a small
server benchmark before attempting large 2D cases.

The 1D benchmark pairs in Table 1 are `(5,15)`, `(7,21)`, `(5,25)`, `(7,35)`,
`(17,51)`, `(5,10)`, `(10,20)`, and `(20,40)`, always passed as
`--coarse M1 --fine M2`. The 2D pairs use `--model 2D --coarse coarse` with
`--fine medium` (49,196) or `--fine fine` (49,441). Run both semantics for each
pair, starting with a small 1D case on the server to confirm the environment.

## Acceptance checks before using a result in the paper

- Record the exact Git commit, solver/Python environment, machine, and thread
  allocation. `git_dirty` must be false on the server checkout.
- The final relation must contain the reported initial pair. For bisection,
  `epsilon_upper` must be feasible, `epsilon_lower` infeasible unless both are
  zero, and their difference must not exceed the requested tolerance.
- Keep the full `history.json` and `relation.csv`; check the relation row count
  against `result.json`. The listed partition state counts exclude one
  absorbing state per model; total state counts include it.
- The baseline currently has no revised tiered acceleration. It fails on
  interval actions with more than 16 successors rather than substituting an
  incomplete vertex set. Report a failure instead of changing the semantics
  or silently dropping vertices.

The fixed-relation Algorithm 2 result is not a global minimum across
relations; Algorithm 3 searches over relations directly.
