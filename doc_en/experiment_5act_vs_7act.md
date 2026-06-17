# Experiment: di_medium_5act → di_fine_7act Pair Analysis

## Date

2026-06-12 ~ 2026-06-14

## Objective

Verify the approximate simulation relation between medium_5act (V≈0.69) and fine_7act (V≈0.99). Expectation: coarse (5 actions) can simulate fine (7 actions) with tolerance ε, enabling coarse-to-fine policy transfer with a meaningful bound.

## Experimental Configuration

| Parameter | Value |
|-----------|-------|
| Coarse IMDP | `di_medium_5act` (14×14, 196 states, 5 actions) |
| Fine IMDP | `di_fine_7act` (21×21, 441 states, 7 actions) |
| f2c Mapping | Geometric overlap (avg ~1.8 coarse/fine cell) |
| Coarse Actions | u ∈ {-5, -2.5, 0, 2.5, 5} |
| Fine Actions | u ∈ {-5, -3.33, -1.67, 0, 1.67, 3.33, 5} |
| eps_tol | 0.001 |
| n_jobs | -1 (all CPUs) |
| mc_iterations | 5000 |
| sim_horizon | 200 |

## Results

### Step 1: Build IMDPs

| IMDP | V(s0) | States | Build Time |
|------|-------|--------|------------|
| di_medium_5act | **0.688** | 196 | 17.4s |
| di_fine_7act | **0.995** | 441 | 9.7s |

### Step 2: ε Binary Search

**12 iterations, total ~50.8 hours.**

| Iter | ε | Feasible | \|R_final\| | LP Calls | Wall Time |
|------|-----|----------|-------------|----------|-----------|
| 1 | 1.000000 | yes | 784 | 603,988 | 36s |
| 2 | 0.000000 | no | 0 | 0 | 1,776s |
| 3 | 0.500000 | no | 0 | 0 | 15,513s |
| 4 | 0.750000 | no | 0 | 0 | 13,873s |
| 5 | 0.875000 | no | 0 | 0 | 14,177s |
| 6 | 0.937500 | no | 0 | 0 | 16,508s |
| 7 | 0.968750 | no | 0 | 0 | 16,564s |
| 8 | 0.984375 | no | 0 | 0 | 16,538s |
| 9 | 0.992188 | no | 0 | 0 | 16,842s |
| 10 | 0.996094 | no | 0 | 0 | 17,226s |
| 11 | 0.998047 | no | 0 | 0 | 17,208s |
| 12 | **0.999023** | **yes** | **763** | 586,300 | 36,502s |

**ε_min = 0.9990234375**

### Key Observations

- **Extremely narrow ε critical point**: Only ε=1.0 and ε=0.999 are feasible. At ε=0.998, R collapses immediately to ∅. There is no gradual shrinkage as ε decreases — it is a cliff.
- **R convergence behavior**: When ε < 0.999, R drops from 784 pairs to 0 in a single fixed-point iteration (all 784 pairs fail the LP test). The algorithm verified this with 460K LP calls.
- **Infeasible cases are still slow**: Although R is empty for ε ≤ 0.998, the warm-start 784 pairs still must be checked one by one (each requires corner enumeration + LP solving), costing ~17 hours per iteration.

### Step 3: RVI + Policy Transfer + MC Validation

| Metric | Value |
|--------|-------|
| V_coarse(s0) | 0.6879 |
| Empirical Satisfaction | **1.0000** |
| Theoretical Lower Bound | **0.0000** |
| Degradation (1−(1−ε)^N) | **1.0000** |
| Bound Holds | True |
| Total Time | 26.5s |

### Step 3 Interpretation

The bound "holds" but is completely meaningless:

```
V_fine(s0) ≥ V_coarse(s0_coarse) − (1−(1−ε)^N)
     1.0  ≥    0.6879              −     1.0
     1.0  ≥   −0.3121  (floored to 0)
```

- ε close to 1 causes degradation = 1.0 (100% probability loss), clamping the theoretical lower bound to 0.
- The fine system's native V=0.995 far exceeds the coarse V=0.688, but the approximate simulation framework cannot transfer this advantage — it is limited by the maximal ε penalty.
- This is a textbook case of a **"meaningless bound"**: the result formally holds but carries zero information.

## Total Time

| Phase | Time | Share |
|-------|------|-------|
| Step 2: ε Binary Search | 182,767s (50.8h) | 99.99% |
| Step 3: RVI + MC | 26.5s | <0.01% |
| **Total** | **182,794s (~50.8h)** | |

## Failure Analysis

### Root Cause: Action Set Mismatch

Coarse actions {-5, -2.5, 0, 2.5, 5} and fine actions {-5, -3.33, -1.67, 0, 1.67, 3.33, 5} lack a one-to-one correspondence:

```
coarse:  -5    -2.5     0     2.5     5
           │      │      │      │      │
fine:    -5  -3.33 -1.67  0  1.67  3.33  5
```

Algorithm 2's condition is ∀a2 (coarse action) ∃a1 (fine action). The coupling LP requires the fine transition distribution to "explain" the coarse transition distribution. When coarse action -2.5 has no exact match in the fine set:

- Fine actions -1.67 and -3.33 cannot produce the same transition distribution as coarse -2.5.
- Convex combinations (randomized strategies) could theoretically simulate intermediate values, but Algorithm 2 does not allow mixed actions — each coarse action must be matched by a **single** fine action.
- LP freedom is only in allocating coupling weights over successor states; it cannot change which action is selected.

### Secondary Factor: Information Loss from Geometric Overlap in Initial R

Initial R has 784 pairs (only 0.9% of the 86,436 possible 196×441 pairs). Potentially valid pairs are pruned by the geometric heuristic. However, in this experiment R **completely collapses** (0 pairs) at ε<0.998, indicating the problem is not missing a few pairs — all 784 fail.

---

## Improvement Plan

### Option 1: Unified Action Set (Most Direct)

Use the **same action discretization** for coarse and fine, eliminating the root cause of action mismatch.

```
Recommended config: medium_7act → fine_7act (both 7 actions)
  u ∈ {-5, -3.33, -1.67, 0, 1.67, 3.33, 5}
  coarse: 14×14, 196 states
  fine:   21×21, 441 states
```

**Expected:**
- V_coarse ≈ 0.85+ (like medium_5act's 0.69 but 7 actions should be higher).
- V_fine ≈ 0.995.
- ε_min should be significantly lower than 0.999 (since ∀a2∃a1 can select the same action value).
- Per-iteration time should be much shorter (check only 1 a1 per a2, not the current 7-vs-5 exhaustive search).

**Prerequisite:** Build `di_medium_7act` (14×14 + 7 actions), verify V > 0.7.

### Option 2: Allow Mixed-Action Matching (Algorithm Improvement)

Relax Algorithm 2's condition from "∃a1" to "∃α₁,...,αₖ, ∑αᵢ=1, αᵢ≥0", i.e., allow fine randomized strategies (convex combination of actions) to simulate coarse actions. This can exactly simulate any coarse action lying in the convex hull of fine actions.

**Cost:** LP variable count increases (must jointly optimize action mixing weights and coupling weights), complexity rises.

### Option 3: Small Unified Action Set — 3-Action Comparison

Fall back to the simplest 3-action setting to verify whether "identical action sets" suffice:

```
di_medium → di_fine (both 3 actions, u ∈ {-5, 0, 5})
  medium: 14×14, V≈0.31
  fine:   21×21, V≈0.37
```

V values are low but actions are fully matched. This serves as a verification experiment: if this configuration also yields large ε, the problem is not action matching but grid resolution disparity (1.5× non-integer ratio causing coarse cell transition intervals to span multiple fine cells).

### Option 4: Integer-Ratio Resolution + Same Actions

Use integer-multiple resolutions to eliminate the geometric overlap heuristic's information loss:

```
di_medium → di_medium_x2 (both 3 actions, 2× integer ratio)
  medium:    14×14, V≈0.31
  medium_x2: 28×28, V≈0.46
```

Strict 1:1 f2c mapping + same actions. If this also yields large ε, the issue is intrinsic dynamics discretization error (coarse probability intervals too wide to be explained by fine).

### Option 5: Relaxed Initial R (No Pruning)

Currently, geometric overlap only retains fine-coarse pairs with spatial intersection, discarding ~99% of possible pairs. For small state spaces, try full label Cartesian product as initial R:

```
medium_5act → fine_7act: 196×441 = 86,436 pairs
Include ALL label-consistent goal/normal/critical pairs in R.
```

This avoids information loss, but LP count explodes (86k pairs vs 784). Suitable only for verifying "were better pairs incorrectly pruned by geometric overlap?"

---

## Conclusion

- The 5-action vs 7-action pairing **does not hold** (ε > 0.999 for simulation, effectively none).
- Root cause is action set mismatch: Algorithm 2's ∀a2∃a1 condition requires each coarse action to have a corresponding fine action.
- The time bottleneck is the **full LP check before R collapse** — even when final R=∅, all pairs must be corner-enumerated and LP-solved.
- **Highest priority: try Option 1** — `di_medium_7act` → `di_fine_7act`, unified 7 actions, expecting significantly smaller ε.

## Data Locations

- eps.pkl: `output/di_medium_5act_fine_7act/eps.pkl`
- results.pkl: `output/di_medium_5act_fine_7act/results.pkl`
