# Large-Scale Run Book — `method='tiered'` (for cluster colleagues)

> ⚠️ **SUPERSEDED (2026-08-02)** — this document is a **competitive-only** runbook
> (pre-cooperative, pre-schema, lazy/tiered Test1D 35→7/51→17 + 2D). It does
> NOT cover the E1–E7 experiment matrix, the §5 machine-readable schema, the
> `--semantics cooperative` path, or probe-trajectory archival.
> **The current experiment spec is [`doc_en/experiment_task_book.md`](../experiment_task_book.md)**
> (E1–E7 matrix + §5 dump schema via `run_experiment.py` + cooperative).
> This document is kept only as a reference for `method='tiered'` semantics and
> the cluster environment setup.

> Run the **sound tiered** coupling check (`method='tiered'`) against the **sound exact
> baseline** (`method='corner'`) on large IMDP approximate-simulation cases, confirm they
> agree on `epsilon_min` / `|R|` (exactness), and collect speedup / residual stats for the
> paper's case study.
>
> Theory (English, already in repo): `doc_en/lazy_enum_review/formal_lower_bound_theorem.md`
> (proven bracket `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB`), `doc_en/Competitive_Approximate_Relation_Computation.md`.
> Full design + small-model results + 2D findings: `doc_en/new_running_example/design.md` (Chinese).

---

## 1. What `method='tiered'` is

A sound + complete per-`(s1,a1,s2,a2)` coupling check that is **never less rigorous** than
Theorem V.3 corner enumeration:

- **Tier 1 (LP-free)** `UB`, `LB_min`: `UB < 1-ε` ⟹ INFEASIBLE (sound); `LB_min ≥ 1-ε` ⟹ FEASIBLE (weak).
- **Tier 1.25 (1 LP)** hardest-corner probe: if the most-likely-violating corner is infeasible ⟹ INFEASIBLE (sound — the feasible-c1 set is convex, P1 = conv(corners)).
- **Tier 1.5 (1 LP)** `LB*`: `LB* ≥ 1-ε` ⟹ FEASIBLE (tightest sound lower bound).
- **Tier 3 (exact)** enumerate all fine corners, `check_coupling` each — **byte-identical to `method='corner'`**.

`tiered == corner` by construction on the residual; the bounds only shortcut cases corner decides
the same way. **k1 ≤ 8** uses all tiers (bounds are cheap); **k1 ≥ 9** skips LB\*+probe (the
2^k1-constraint LB\* LP is a liability at large k1 / tight ε) — only `UB` + corner-enum. Skipping
LB\* only adds enumeration ⟹ still sound + complete, still `tiered == corner`.

## 2. Environment

```bash
# Windows (this laptop):
PYTHON="C:/Users/DWJ/.conda/envs/dyabstract/python.exe"
# Cluster (Linux): activate a conda env with cvxpy + jax + scipy + numpy + tqdm
cd imdp-synthesis   # repo root

# Smoke test (should print three-way PASS):
$PYTHON doc_en/new_running_example/run_running_example_pipeline.py
```

## 3. Code status (ready, small models verified bug-free)

New/modified: `core/approx_sim/coupling_tiered.py` (new), `core/approx_sim/algorithm.py`
(`method='tiered'` arm), `time_algorithm2.py` (`--method tiered`), `compare_methods.py`
(`corner` vs `tiered`, per-iteration PASS/FAIL, now takes `n_fine n_coarse` args),
`check_tiered_soundness.py` (new, per-sub-pair vs exact g), `run_running_example_pipeline.py` (new).
Unchanged/reused: `coupling_bounds.py`, `coupling.py`, `epsilon_search.py`, `corners.py`.

**Verified on small models (this laptop, no bug):**

| Case | Check | Result |
|---|---|---|
| running example (tweaked δ, 3-state) | tiered == corner == hand-calc (per-pair g, ε_min=0.1, fixed-ε retain/remove) | **PASS** |
| Test1D 15→5 (k1≤5) | full ε-search tiered==corner (ε_min=0.000977, |R|=15, 12 iters 0 mismatch) | **PASS** (LP 1.70×↓) |
| Test1D 15→5 | per-sub-pair tiered vs exact g (ε=0.05/0.1/0.5) | **PASS** (0 false-feas, 0 false-infeas) |
| Test1D 21→7 (k1=5) | full ε-search tiered==corner (ε_min=0.000977, |R|=21, 0 mismatch) | **PASS** (LP 1.43×↓) |

Same code path is used at scale ⟹ no new bug risk.

## 4. Commands to run on the cluster

> **Run corner and tiered SEPARATELY (sequentially), not concurrently.** Both use `n_jobs=-1`
> (all CPUs); running them together starves both. IMDP builds are cached in `.cache_imdps/`
> (loaded in seconds on the 2nd run).

### 4.0 Experiment plan at a glance

The experiments below go small→large. **Purpose** = why we run it; **Expected** = what a correct
(sound+complete) result looks like. Run them in order; stop and report if any **Expected** fails
(that signals a bug).

| # | Experiment | Purpose | Command (run corner & tiered) | Expected result | ~Time |
|---|---|---|---|---|---|
| 0 | Smoke test | Confirm the code is sound + correct on a tiny case | `python doc_en/new_running_example/run_running_example_pipeline.py` | three-way PASS: `tiered == corner == hand-calc`, ε_min=0.1, \|R\|=3 at ε≥0.1 / 2 at ε<0.1 | seconds |
| 1 | Test1D 35→7 | exactness `tiered==corner` at k1=7-8 (keeps LB\*+probe) | `compare_methods.py 35 7` | `[PASS] tiered == corner`; ε_min & \|R\| match; 0 trajectory mismatch | minutes |
| 2 | Test1D 51→17 | exactness `tiered==corner` at k1=9 (skips LB\*+probe) | `compare_methods.py 51 17` | `[PASS]`; ε_min & \|R\| match; 0 mismatch | minutes |
| 3 | Test1D per-sub-pair soundness | prove 0 false-feasible & 0 false-infeasible at the K_LBSTAR=8 boundary | `check_tiered_soundness.py 35 7 0.1` and `... 51 17 0.1` | `0 false-feasible + 0 false-infeasible` | 1-2 min each |
| 4 | 2D 49→441 (main case study) | get the case-study ε_min + tiered-vs-corner speedup; demonstrate the §3 barrier | `time_algorithm2.py --coarse_resolution coarse --fine_resolution fine --method {corner,tiered}` | ε_min & \|R\| **match**; ~2.5 h/method; tiered shortcuts the infeasible-side ε-iters (UB, 0 enum) | ~2.5 h/method |
| 5 | 2D 196→441 (the 50.8 h case) | demonstrate the infeasible-side speedup at scale | `time_algorithm2.py --coarse_resolution medium --fine_resolution fine --method {corner,tiered}` | ε_min & \|R\| match; tiered much faster on infeasible ε-iters (the ~40 h of the original) | very long |

**Deliverable per experiment**: case + method + `epsilon_min` / `|R_final|` / `total wall time` /
`total LP calls` + the `[PASS/FAIL]` line (see §8). These populate the paper's case-study tables.

Detailed commands and per-experiment notes follow (§4.1–§4.4 = experiments 1–5).

### 4.1 Test1D mid-scale (~minutes each) — covers the K_LBSTAR=8 boundary

**Purpose:** confirm `tiered == corner` exactness across the k1 threshold — k1=7-8 (35→7) keeps
LB\*+probe, k1=9 (51→17) skips them. Both paths must agree with corner.

```bash
$PYTHON compare_methods.py 35 7     # k1=7-8 -> keeps LB*+probe
$PYTHON compare_methods.py 51 17    # k1=9   -> skips LB*+probe
# optional stricter per-sub-pair check (experiment 3):
$PYTHON check_tiered_soundness.py 35 7 0.1
$PYTHON check_tiered_soundness.py 51 17 0.1
```
**Expected:** `[PASS] tiered == corner: exact match` + `per-iteration trajectory: MATCH`.
ε_min and |R| must match exactly (values change with scale; only consistency is asserted).
Per-sub-pair: `0 false-feasible + 0 false-infeasible`.

### 4.2 2D DoubleIntegrator 49→441 (main case-study case, ~2.5 h per method)

**Purpose:** the paper's main case-study result — ε_min/|R|, the tiered-vs-corner speedup, and a
live demonstration of the §3 barrier (tight-ε feasible core is irreducible for sound methods).

```bash
$PYTHON time_algorithm2.py --coarse_resolution coarse --fine_resolution fine --method corner  --eps_tol 1e-3
$PYTHON time_algorithm2.py --coarse_resolution coarse --fine_resolution fine --method tiered --eps_tol 1e-3
```
**Expected:** (both `TIMING SUMMARY` blocks) `Epsilon minimum` and `|R_final|` **must match**
between the two methods; record `total wall time`, `Phase 3` time, the per-ε table
(`LP calls` / `wall time`), and the tiered-vs-corner LP-reduction / speedup ratios.

**Expected behavior** (measured, see design.md §12): fine k1=9–12, ~398k corners (max 1408 per
(s,a)); the tight-ε feasible core (387-corner enum) dominates ⟹ both methods ~2.5 h (§3 barrier,
irreducible for sound methods). tiered shortcuts the infeasible-side ε-iters via UB (0 enum);
the tight-ε feasible core still enumerates (same as corner). At ε=0.0, tiered may be slightly
slower than corner (UB is loose at large k1; the 4096-subset LP-free bound is overhead that
doesn't certify) — this is the §2.6 regime (bounds don't help at large k1 / tight ε), **not a bug**.

### 4.3 2D DoubleIntegrator 196→441 (the 50.8 h case — very long)

**Purpose:** demonstrate that `tiered`'s UB pre-filter dramatically speeds up the infeasible-side
ε-iters at scale (the ~40 h of the original 50.8 h corner run), while the ε_min feasible iter still
enumerates (§3 barrier).

```bash
$PYTHON time_algorithm2.py --coarse_resolution medium --fine_resolution fine --method corner  --eps_tol 1e-3
$PYTHON time_algorithm2.py --coarse_resolution medium --fine_resolution fine --method tiered --eps_tol 1e-3
```
**Expected:** same checks as 4.2 — ε_min & |R| match; tiered much faster on infeasible ε-iters
(UB, 0 enum); the ε_min feasible iter still enumerates. Run only with ample cluster budget.

### 4.4 Optional YAML pipeline (alternative entry point)

```bash
$PYTHON run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine   # 49->441
$PYTHON run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine   # 196->441
```
Set `method: tiered` in the yaml build/pair as needed. (Same cases as 4.2/4.3, alternative CLI.)

## 5. PASS criteria (exactness)

For each case, compare the two outputs:
1. `epsilon_min`: `abs(corner - tiered) <= eps_tol` (usually exactly equal, since Tier 3 == corner).
2. `|R_final|`: equal.
3. `compare_methods.py` prints `[PASS] tiered == corner` + `0 mismatches` automatically.
4. (stricter) `check_tiered_soundness.py`: `0 false-feasible + 0 false-infeasible`.

Any mismatch = bug — please report the case's `epsilon_min` / `|R|` / mismatch line.

## 6. Known behavior / caveats (NOT bugs)

- **`K_LBSTAR = 8`** (`coupling_tiered.py`): k1≥9 skips LB\*+probe. Raise it to use LB\* at
  larger k1, but k1≥10 makes the 2^k1-constraint LB\* LP slower than corner's short-circuit at
  tight ε (design.md §12.6).
- **UB overhead at large k1 / tight ε**: at k1=12, Tier 1 enumerates 2^12=4096 subsets in pure
  Python (~50 ms/sub-pair); when UB is loose (common at tight ε) it doesn't certify and is overhead.
  To get pure corner speed on 2D, also gate Tier 1 on `k1 <= K_LBSTAR` (large-k1 -> pure
  corner-enum); soundness unchanged.
- **halfspace soundness**: these cases have k1 ≤ 12 (greedy, sound), so `corners.py`'s halfspace
  / `_enumerate_lp` fallback is NOT hit. If a large case has k1 > 12, the halfspace path silently
  falls back to the **unsound** `_enumerate_lp` when `HalfspaceIntersection` throws (roadmap Step 6,
  unfixed) — please report; it should be changed to raise.
- **`method='lazy'` is still unsound** — do not use it for results (only `corner` / `tiered` are sound).
- **CPU contention**: corner/tiered both `n_jobs=-1` — run sequentially, never concurrently.

## 7. Utility: probe k1 before running

```bash
$PYTHON probe_k1.py    # reports k1 / corner-count distribution for the cached 49->441 IMDPs
```
(For other cases, adapt the cache path / build IMDPs inline.) Lets you anticipate whether
halfspace (k1>12) or bounds-skip (k1>22) will trigger before committing a long run.

## 8. Feedback format

Per case, please return: case + method + `epsilon_min` / `|R_final|` / `total wall time` /
`total LP calls`; the `[PASS/FAIL]` line (or manual comparison); and any exception/mismatch lines.
These numbers populate the paper's case-study tables (design.md §11/§12 has the small-model +
2D-behavior framework).
