# IMDP Approximate Simulation — Step-by-Step Workflow

The full pipeline is split into three independent steps. Each IMDP build is independent — fine and coarse are two symmetric build processes, each saved to its own folder.

## Table of Contents

> Document index: see [README.md](README.md), which catalogs all doc/ files and their recommended reading order.
>
> New collaborators should follow the reading order in README.md for quick alignment.

- [Full Case Study: DoubleIntegrator coarse→coarse](#full-case-study-doubleintegrator-coarsecoarse)
- [Core Philosophy](#core-philosophy)
- [Two Ways to Run](#two-ways-to-run)
- [Resolution Options](#resolution-options)
- [Step Details](#step-details)
- [YAML Configuration](#yaml-configuration)
- [Data Flow & File Structure](#data-flow--file-structure)
- [Typical Usage Scenarios](#typical-usage-scenarios)
- [Run Log (log.md)](#run-log)
- [Key Metrics Reference](#key-metrics-reference)

---

## Full Case Study: DoubleIntegrator coarse→coarse

This section walks through the complete process from scratch to bound verification, using the `demo` configuration (DoubleIntegrator 2D system, coarse→coarse, 49→49 states) as a worked example.

### Background

- **System**: DoubleIntegrator 2D continuous dynamics, control input u∈[-5,5], state space [-21,-10.5]×[21,10.5].
- **Target Region**: [-4,-2]×[4,2].
- **Initial State**: x0 = [0, -8].
- **Discrete Actions**: 3 (u ∈ {-5, 0, 5}).
- **Coarse IMDP**: 7×7 grid → 49 abstract states.
- **Fine IMDP**: Also 7×7 grid (demo uses same resolution to verify pipeline correctness).
- **Expected Result**: Same grid should admit exact simulation (ε=0), MC validation should confirm the bound holds.

### System Model

```
Boundary:  [-21, -10.5] × [21, 10.5]
Target:    [-4, -2] × [4, 2]         (small rectangle, upper right)
Initial:   x0 = [0, -8]               (lower right)
Actions:   3 discrete control inputs u ∈ {-5, 0, 5}
```

The continuous state space is partitioned into a 7×7 rectangular grid (49 cells). Each cell is labeled as goal, critical (boundary), or normal. IMDP transition probability intervals are computed from forward reachability of the continuous dynamics under each action.

### Step 1: Build IMDP

Build the coarse-resolution IMDP, automatically running RVI to check V(s0).

```bash
$ python run_pipeline.py build --config configs/approx_sim.yaml di_coarse
```

Output:

```
STEP 1: Build IMDP + V check
  Model:      DoubleIntegratorApproxSim
  Resolution: coarse
  Output:     output/di_coarse

--- Creating model ---
Model: 0.6s
Partition: 49 states (2.9s)
Forward reachability: 0.3s
Computing probability intervals (JAX may compile)...
Probability intervals: 1.9s

Build complete: 49 states, 6.2s

--- Running RVI to check V > 0 ---
Converged after 7 iterations
RVI: 0.8s  V(s0) = 0.000000  V>0 = True

STEP 1 complete — 7.1s total
  States:  49
  V(s0):   0.000000  (viable=True)
  Output:  output/di_coarse/
```

Generated file `output/di_coarse/params.yaml`:

```yaml
model: DoubleIntegratorApproxSim
resolution: coarse
seed: 42
num_states: 49
V_s0: 5.194038976696902e-08
V_viable: true
build_time_s: 6.2
rvi_time_s: 0.8
total_time_s: 7.1
```

Key points:
- 49-state coarse IMDP built in 6.2s, RVI check in 0.8s.
- V(s0)=5.19e-08 (numerically >0), V_viable=true, can proceed.

### Step 2: ε Binary Search

Search for the minimum tolerance ε such that coarse IMDP simulates fine IMDP. For same grid (coarse→coarse), expect ε_min=0 (exact simulation).

```bash
$ python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

Step 2 output:

```
STEP 2: Epsilon Search (Algorithm 2)
  Fine IMDP:   output/di_coarse/imdp.pkl
  Coarse IMDP: output/di_coarse/imdp.pkl
  Eps tol:     0.001

--- Building f2c mapping ---
  Mapped: 49/49 fine states (0.6s)

--- Epsilon Search ---
Verifying epsilon=1.0 (upper bound)...
Initial R: 49 / 49 pairs (label-consistent f2c)
  Iter 0: checked 49 pairs, removed 0, |R|=49, 1190 LPs (0.8s)
    Profile: max_k1=9, max_corners=51, corner_enum=0.3s, lp_solve=0.0s

Testing epsilon=0.0 (lower bound)...
Warm-start R: 49 pairs (from previous epsilon)
  Iter 0: checked 49 pairs, removed 0, |R|=49, 1771 LPs (12.2s)
    Profile: max_k1=9, max_corners=51, corner_enum=0.5s, lp_solve=11.6s

Epsilon minimum = 0.0 (strict simulation possible)
```

Binary search process:

| ε | Feasible? | \|R\| | LP Calls | Wall Time |
|---|-----------|------|---------|-----------|
| 1.0 | yes | 49 | 1,190 | 0.8s |
| 0.0 | yes | 49 | 1,771 | 12.2s |

Result: **ε_min = 0.0**, same grid admits exact simulation, initial state pair (21, 21) ∈ R.

### Step 3: RVI + Policy Transfer + MC Validation

```
STEP 3: RVI + Policy Transfer + MC Validation
  Fine IMDP:   output/di_coarse/imdp.pkl
  Coarse IMDP: output/di_coarse/imdp.pkl
  Epsilon:     output/demo/eps.pkl

--- RVI on Coarse IMDP ---
Converged after 7 iterations
  RVI done: 1.5s
  V_coarse[s0=21] = 0.000000

--- Policy Transfer ---
  Transfer done: 0.1s

--- MC Validation (5000 rollouts, horizon=200) ---
  MC done: 127.4s
  Empirical satisfaction:  0.9794
  Theoretical lower bound: 0.0000
  V_coarse(s0):            0.0000
  Degradation (1-(1-eps)^N): 0.0000
  Bound holds:             True
```

### Complete Results Summary

| Phase | Key Result | Time |
|-------|-----------|------|
| Step 1: Build IMDP | 49 states, V(s0)≈5.2e-08 | 7.1s |
| Step 2: ε Search | ε_min=0.0, \|R\|=49, exact simulation | 12.2s |
| Step 3: RVI | V_coarse(s0)=0, policy converged | 1.5s |
| Step 3: Policy Transfer | 49 state policies mapped | 0.1s |
| Step 3: MC Validation | 5000×200 rollouts | 127.4s |
| **Total** | **bound_holds=True** | **~149s** |

### Result Interpretation

1. **ε_min = 0.0**: Exact simulation exists between two IMDPs on the same grid. This is expected — with identical resolution, the f2c map is one-to-one, and Algorithm 2 converges in the first iteration.

2. **bound_holds = True**: Empirical satisfaction probability (0.9794) ≥ theoretical lower bound (0.0000). Theoretical V_coarse(s0) is near 0 (coarse abstraction is too conservative), but MC simulation shows the real system reaches the goal 97.9% of the time, confirming good controllability.

3. **degradation = 0.0**: Since ε=0, approximate simulation introduces no probability loss ((1-(1-0)^200)=0).

4. **Bottleneck analysis**: Step 2 LP solving accounts for 93% of ε search time (11.6s/12.2s), corner enumeration only 3%. With denser fine grids, successor count k1 increases, corner count grows exponentially as 2^(k1-1), and LP count explodes. This is the combinatorial lower bound imposed by the Minkowski-Weyl theorem.

### Key Takeaways

- For coarse→coarse (same grid), Algorithm 2 verifies existence of **exact simulation** with zero tolerance.
- The policy transfer bound **holds empirically** in MC simulation, validating the theoretical framework.
- The full pipeline completes in **149s**, suitable as a fast regression test for framework correctness.
- Using denser fine grids (e.g., coarse→fine) will dramatically increase Step 2 LP solving time, requiring further optimization strategies.

---

## Core Philosophy

**Fine and Coarse are relative.** Each IMDP is simply an abstraction at a particular resolution — neither is inherently "fine" or "coarse". Therefore:

- **Step 1 builds one IMDP at a time**, independently at the given resolution, and immediately runs RVI to check V(s0) > 0.
- **V>0 pre-check is critical**: if the coarse IMDP has V=0 (too coarse, no feasible reach-avoid strategy), then ε search and policy transfer are meaningless.
- **Only when both IMDPs satisfy V>0 is it worth running Step 2 ε search.**

Actual workflow:

```
Step 1: Build IMDP_A → RVI check V_A > 0 ?
Step 1: Build IMDP_B → RVI check V_B > 0 ?
    ↓
  ┌─ Either V=0 → Stop, adjust resolution/parameters
  │
  └─ Both V>0 → Step 2: ε search → Step 3: Policy transfer + MC
```

---

## Two Ways to Run

### Method A: run_pipeline.py (Recommended)

```bash
# List all predefined configs
python run_pipeline.py --config configs/approx_sim.yaml --list

# Build a single IMDP
python run_pipeline.py build --config configs/approx_sim.yaml di_coarse
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# Pair analysis (auto-checks V>0, builds missing IMDPs if needed)
python run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine

# Run only a specific step
python run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine --step 2
```

### Method B: Manual Step-by-Step

Call `steps/` scripts individually, suitable for debugging and custom parameters.

```bash
# Step 1: Build a single IMDP
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution coarse \
    --output output/di_coarse

python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution fine \
    --output output/di_fine

# Step 2: ε search
python steps/step2_epsilon_search.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --output output/di_coarse_fine/eps.pkl

# Step 3: Policy transfer + MC validation
python steps/step3_validate.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --eps output/di_coarse_fine/eps.pkl \
    --output output/di_coarse_fine/results.pkl
```

---

## Resolution Options

Available resolutions for the DoubleIntegrator 2D system:

### Base Resolutions (3 Actions)

| Value | Grid | States | Notes |
|-------|------|--------|-------|
| `coarse` | 7×7 | 49 | Fastest, for verifying pipeline |
| `medium` | 14×14 | 196 | |
| `fine` | 21×21 | 441 | |
| `medium_x2` | 28×28 | 784 | |
| `fine_x2` | 42×42 | 1,764 | Densest, Algorithm 2 slowest |

### Multi-Action Variants (5 / 7 Actions)

More discrete actions improve strategy expressiveness, yielding higher V(s0):

| Value | Grid | Actions | States | V(s0) |
|-------|------|---------|--------|-------|
| `medium_5act` | 14×14 | 5 | 196 | **0.688** |
| `fine_7act` | 21×21 | 7 | 441 | **0.995** |

Action discretization:
- 3 actions: u ∈ {-5, 0, 5}
- 5 actions: u ∈ {-5, -2.5, 0, 2.5, 5}
- 7 actions: u ∈ {-5, -3.33, -1.67, 0, 1.67, 3.33, 5}

All resolutions share the same dynamics parameters: control input u∈[-5,5], boundary [-21,-10.5]×[21,10.5], target region [-4,-2]×[4,2], initial state x0=[0,-8].

---

## f2c Mapping: Geometric Overlap vs Integer Multiple

### Problem

Initially, `build_fine_to_coarse_map` required the fine grid dimension to be an exact integer multiple of the coarse grid dimension in each axis (e.g., 14/7=2, 42/21=2). This restricted which resolution pairs could be compared — for instance, medium (14) and fine (21) have ratio 1.5, which would error out.

### Root Cause Analysis

R initialization only requires label consistency, not geometric containment. But pure label Cartesian product causes |R| explosion (medium→fine ~55,000 pairs), intractable.

### Solution: Geometric Overlap Mapping

`build_f2c_overlap_map` finds, for each fine cell, all coarse cells whose spatial region overlaps with it. For a 2D system:

```
Non-integer ratio (21→14, 1.5×):
┌─────┬─────┐
│ fine  │ fine  │      Each fine cell overlaps at most
│ → c1  │ → c2  │      4 coarse cells
│ → c3  │ → c4  │
├─────┼─────┤      avg ~1.8 coarse/fine
│ fine  │ fine  │      Initial R ~794 pairs (tractable)
└─────┴─────┘

Integer ratio (14→7, 2×):
┌───┬───┐
│ fine │ fine │        Each fine cell overlaps exactly
│  →   │  →   │        1 coarse cell
├───┼───┤             avg = 1.0 coarse/fine
│ fine │ fine │        (degenerates to original f2c)
└───┴───┘
```

- Integer ratio: avg overlap = 1.0, degenerates to original strict 1:1 mapping.
- Non-integer ratio: avg overlap ≤ 4 (2D), R size tractable, and no loss of label completeness in theory.
- **Note**: This is a heuristic pruning — even without spatial overlap, two states can be canonically valid pairs. Hence the computed ε may be conservative (overestimated), but the bound still holds. This is a computation-for-completeness tradeoff.

---

## Step Details

### Step 1 — Build Single IMDP + V>0 Check

**What it does:** Build one IMDP at a given resolution, run RVI to check whether V(s0) > 0.

**Internal flow:**

```
1. create_model(args)              → Dynamics model
2. RectangularPartition(model)     → Rectangular grid partition
3. RectangularForward(...)         → Forward reachable set per cell
4. compute_probability_intervals() → Transition probability intervals
5. IMDP(...)                       → Wrap as IMDP object
6. RVI_JAX(imdp, s0)              → V(s0) value function
7. Save imdp.pkl + params.yaml
```

**Command-line arguments:**

| Argument | Description |
|----------|-------------|
| `--model` | Model name, default `DoubleIntegratorApproxSim`, also `Dubins3DApproxSim` |
| `--resolution` | Resolution name (required) |
| `--output` | Output directory path (required, auto-created) |
| `--seed` | Random seed, default `42` |

**Output files:**

`imdp.pkl` contains:

| Key | Type | Purpose |
|-----|------|---------|
| `imdp` | `IMDP` | IMDP object |
| `partition` | `RectangularPartition` | Grid partition |
| `model` | `Dynamics` | Dynamics model |
| `resolution` | `str` | Resolution name |
| `model_name` | `str` | Model class name |

`params.yaml` contains:

| Key | Description |
|-----|-------------|
| `model` | Model name |
| `resolution` | Resolution |
| `seed` | Random seed |
| `num_states` | Number of states |
| `V_s0` | Robust value at initial state |
| `V_viable` | Whether V(s0) > 0 |
| `build_time_s` | Build wall time |
| `rvi_time_s` | RVI wall time |
| `total_time_s` | Total wall time |

**Timing estimates:**

| Resolution | States | Time |
|------------|--------|------|
| coarse | 49 | ~6s |
| medium | 196 | ~7s |
| fine | 441 | ~9s |
| fine_x2 | 1764 | ~15s |

Time is dominated by `compute_probability_intervals` (JAX vectorized transition interval computation) and first-time JAX compilation. RVI check is fast (~0.8s for coarse).

---

### Step 2 — ε Binary Search

**What it does:** Load two IMDPs, build the f2c map, run Algorithm 2 fixed-point iteration + ε binary search to find the minimal ε.

**Core concept:**

ε is the tolerance parameter for approximate simulation. Coupling distribution W has mass ≥ 1−ε within relation R:
- ε=0 → exact simulation (100% of W's mass in R).
- ε=1 → unconstrained (any pair is in R).
- ε_min → the tightest tolerance at which the coarse abstraction "simulates" the fine system.

**Binary search strategy:**

```
Known hi=1.0 always feasible (upper bound)
Test lo=0.0 → if feasible then ε_min=0 (exact simulation)
Otherwise binary search in [lo, hi]:
  mid = (lo+hi)/2
  Run Algorithm 2(mid) → check (s0_fine, s0_coarse) ∈ R(mid) ?
    feasible → hi=mid (tighten)
    infeasible → lo=mid (too tight)
  Repeat until hi-lo ≤ eps_tol
```

Exploits monotonicity R(ε_small) ⊆ R(ε_large): warm-start R_hi when testing ε_mid.

**Command-line arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--imdp_fine` | — | Fine IMDP `.pkl` file (required) |
| `--imdp_coarse` | — | Coarse IMDP `.pkl` file (required) |
| `--output` | — | Output `.pkl` file path (required) |
| `--eps_tol` | `1e-3` | Binary search precision |
| `--n_jobs` | `-1` | Parallel threads, `-1`=all CPUs, `1`=sequential |

**Output file contents:**

| Key | Type | Description |
|-----|------|-------------|
| `epsilon_min` | `float` | Minimum ε |
| `R_final` | `set[(int,int)]` | Final simulation relation |
| `eps_history` | `list[dict]` | Per evaluation: ε, feasible, n_pairs, lp_calls, wall_time |
| `s0_fine` | `int` | Fine initial state |
| `s0_coarse` | `int` | Coarse initial state |
| `init_in_R` | `bool` | Whether initial state pair is in R |

**Bottleneck analysis:**

| Metric | ε=1.0 (trivial) | ε=0.0 (strict) |
|--------|-----------------|----------------|
| Corner enum time | 0.3s (3%) | 0.5s (4%) |
| LP solve time | 0.0s (0%) | 11.6s (95%) |
| LP calls | 1,190 | 1,771 |
| max_k1 | 9 | 9 |
| max_corners | 51 | 51 |

**The bottleneck is LP solving (~95%), not corner enumeration.** Denser grids → larger successor count k1 → corner count grows exponentially (2^(k1-1)) → LP count explodes.

---

### Step 3 — RVI + Policy Transfer + MC Validation

**What it does:** Solve robust value iteration on the coarse IMDP, transfer the optimal policy to the fine IMDP, validate the bound via Monte Carlo simulation.

**Internal flow:**

```
1. build_f2c_overlap_map()          → f2c mapping
2. RVI_JAX(imdp_coarse, s0)          → V_coarse, policy_coarse
3. transfer_policy(policy_coarse)    → policy_fine
4. validate_transfer(...)             → MC simulation + bound verification
```

**Theoretical bound:**

```
V_fine(s0) ≥ V_coarse(s0_coarse) − (1 − (1−ε_min)^N)
```

where N is the horizon. MC validation checks whether empirical satisfaction probability ≥ lower bound.

**Command-line arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--imdp_fine` | — | Fine IMDP `.pkl` file (required) |
| `--imdp_coarse` | — | Coarse IMDP `.pkl` file (required) |
| `--eps` | — | Step 2 output `.pkl` file (required) |
| `--output` | — | Output `.pkl` file path (required) |
| `--mc_iterations` | `5000` | Number of MC rollouts |
| `--sim_horizon` | `200` | Simulation horizon |
| `--skip_mc` | — | Skip MC validation (debug mode, saves ~2min) |

**Output file contents:**

| Key | Type | Description |
|-----|------|-------------|
| `V_coarse` | `np.array` | Coarse IMDP value function |
| `policy_coarse` | `np.array` | Coarse policy labels |
| `policy_fine` | `np.array` | Transferred fine policy labels |
| `validation` | `dict` or `None` | `empirical_prob`, `theoretical_bound`, `bound_holds`, `degradation` |

---

## YAML Configuration

The config file [configs/approx_sim.yaml](../configs/approx_sim.yaml) has two sections:

### builds — Single IMDP Builds

```yaml
builds:
  di_coarse:
    model: DoubleIntegratorApproxSim
    resolution: coarse
    seed: 42
    output_dir: output/di_coarse
```

### pairs — Pair Analysis

```yaml
pairs:
  demo:
    coarse_build: di_coarse
    fine_build: di_coarse
    output_dir: output/demo
    eps_tol: 0.001
    n_jobs: -1
    mc_iterations: 5000
    sim_horizon: 200
    skip_mc: false
```

### Predefined Configs at a Glance

**Builds:**

| Config | Resolution | States | V(s0) |
|--------|-----------|--------|-------|
| `di_coarse` | coarse | 49 | ~0 |
| `di_medium` | medium | 196 | 0.314 |
| `di_fine` | fine | 441 | 0.373 |
| `di_medium_x2` | medium_x2 | 784 | — |
| `di_fine_x2` | fine_x2 | 1,764 | — |
| `di_medium_5act` | medium_5act | 196 | **0.688** |
| `di_fine_7act` | fine_7act | 441 | **0.995** |

**Pairs:**

| Config | Coarse→Fine | Purpose |
|--------|-------------|---------|
| `demo` | coarse→coarse (49→49) | Full case study pipeline verification |
| `di_coarse_fine` | coarse→fine (49→441) | Small scale (coarse V≈0, unsuitable) |
| `di_medium_fine` | medium→fine (196→441) | Non-integer ratio case (1.5×) |
| `di_medium_fine_x2` | medium→fine_x2 (196→1764) | Medium scale |
| `di_fine_fine_x2` | fine→fine_x2 (441→1764) | Larger scale |
| `di_medium_5act_fine_7act` | medium_5act→fine_7act (196→441) | **Recommended: multi-action high V** |

---

## Data Flow & File Structure

```
configs/approx_sim.yaml          ← Unified parameter management
steps/
  step1_build_imdp.py             ← Step 1: Build single IMDP + V>0 check
  step2_epsilon_search.py         ← Step 2: ε search (loads two IMDPs)
  step3_validate.py               ← Step 3: RVI + policy transfer + MC
run_pipeline.py                   ← Reads YAML, orchestrates three steps

                    ┌──────────────────────┐
  config.yaml  ──→  │    run_pipeline.py   │
                    └──────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          build IMDP      build IMDP       PAIR RUN
          (coarse)        (fine)           ├─ Step 2
              │               │            └─ Step 3
              ▼               ▼
      output/di_coarse/  output/di_fine/
        imdp.pkl           imdp.pkl
        params.yaml        params.yaml
              │               │
              └───────┬───────┘
                      ▼
              output/di_coarse_fine/
                eps.pkl
                results.pkl
```

**File reuse:** The same IMDP pair can drive multiple ε searches (different `eps_tol`), and the same `imdp + eps` pair can repeatedly run Step 3 (varying `mc_iterations`, `sim_horizon`).

---

## Typical Usage Scenarios

### Scenario 1: Quick V > 0 Check

```bash
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution coarse \
    --output output/test_coarse

# Inspect params.yaml
cat output/test_coarse/params.yaml
# Look at V_s0 and V_viable fields
```

### Scenario 2: Run Full Case Study

```bash
python run_pipeline.py build --config configs/approx_sim.yaml di_coarse
python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

### Scenario 3: Non-Integer Ratio Practical Run (medium→fine, 1.5×)

Both IMDPs have V>0; uses geometric overlap mapping to bypass integer ratio restriction:

```bash
# Build IMDPs
python run_pipeline.py build --config configs/approx_sim.yaml di_medium
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# Check V values
cat output/di_medium/params.yaml  # V(s0) = 0.314
cat output/di_fine/params.yaml    # V(s0) = 0.373

# Run pair
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine
```

### Scenario 4: Iterative Parameter Tuning (No Rebuild)

```bash
# Build IMDPs once
python run_pipeline.py build --config configs/approx_sim.yaml di_medium
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# Repeatedly run Step 2 with different parameters
python steps/step2_epsilon_search.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_medium/imdp.pkl \
    --output output/di_medium_fine/eps_tol4.pkl \
    --eps_tol 1e-4

python steps/step2_epsilon_search.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_medium/imdp.pkl \
    --output output/di_medium_fine/eps_seq.pkl \
    --n_jobs 1
```

### Scenario 5: Validate Bound Only (Skip MC)

```bash
python steps/step3_validate.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --eps output/di_coarse_fine/eps.pkl \
    --output output/di_coarse_fine/results.pkl \
    --skip_mc
```

### Scenario 6: Full MC Validation

```bash
python steps/step3_validate.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --eps output/di_coarse_fine/eps.pkl \
    --output output/di_coarse_fine/results.pkl \
    --mc_iterations 10000 --sim_horizon 300
```

### Scenario 7: Recommended — Multi-Action High V (medium_5act→fine_7act)

This is the currently recommended complete case study combination. Coarse IMDP V≈0.69, fine IMDP V≈0.99 — both have reliable reach-avoid strategies:

```bash
# Step 1: Build both IMDPs (each includes V>0 check)
python run_pipeline.py build --config configs/approx_sim.yaml di_medium_5act
python run_pipeline.py build --config configs/approx_sim.yaml di_fine_7act

# Confirm V values
cat output/di_medium_5act/params.yaml  # V(s0) ≈ 0.688
cat output/di_fine_7act/params.yaml    # V(s0) ≈ 0.995

# Step 2+3: Pair analysis
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_5act_fine_7act
```

Expected results:
- coarse V≈0.69 → coarse strategy has ~69% probability of reaching goal.
- fine V≈0.99 → fine strategy almost certainly reaches goal.
- ε_min may be small (fine's 7 actions can "simulate" coarse's 5 actions reasonably well).
- bound: V_fine ≥ 0.69 − (1−(1−ε)^200), negligible loss when ε is small.

---

## Run Log

Detailed build records and pair analysis results are in [log.md](log.md), including:

- Environment info (git commit, Python/JAX versions).
- V(s0) and timing for all built IMDPs.
- ε search process and MC validation results for each pair analysis.
- Summary comparison table.

Append results to the relevant entries in log.md after each new configuration run.

---

## Key Metrics Reference

### params.yaml (Step 1 Output)

| Metric | Meaning |
|--------|---------|
| `V_s0` | Robust maximum reach probability at initial state |
| `V_viable` | Whether V(s0) > 0. If false, need a denser resolution |
| `num_states` | Number of IMDP states |

### Step 2 Output

| Metric | Meaning |
|--------|---------|
| `epsilon_min` | Minimum tolerance for coarse to simulate fine. Smaller is better |
| `\|R_final\|` | Number of state pairs in the simulation relation |
| `LP calls per ε` | LP call count. Largest at ε=0.0 |
| `max_k1` | Number of fine successors for one (s,a). Determines corner count (2^(k1-1)) |
| `max_corners` | Maximum corners for one (s,a). Determines worst-case LP count |

### Step 3 Output

| Metric | Meaning |
|--------|---------|
| `V_coarse(s0)` | Coarse IMDP robust maximum reach probability |
| `empirical_prob` | Actual goal-reaching frequency in MC simulation of fine system |
| `theoretical_bound` | V_coarse − (1−(1−ε)^N), the theoretical lower bound |
| `bound_holds` | Whether `empirical_prob ≥ theoretical_bound` |
| `degradation` | (1−(1−ε)^N), probability loss introduced by approximate simulation |
