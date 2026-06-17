# IMDP Approximate Simulation — Run Log

## Environment

| Item | Value |
|------|-------|
| Date Range | 2026-06-08 ~ 2026-06-14 |
| Git Commit | `75bc0d7` — Add DoubleIntegrator model + fix corner enumeration correctness |
| OS | Ubuntu 22.04.5 LTS |
| Python | 3.13.13 |
| JAX | 0.9.2 |
| Conda Env | `dyabstract` |

---

## Step 1: IMDP Build Records

### DoubleIntegrator 3 Actions (u ∈ {-5, 0, 5})

| Config | Resolution | Grid | States | V(s0) | V>0 | Build Time | RVI Time | Total Time | Output |
|--------|-----------|------|--------|-------|-----|------------|----------|------------|--------|
| `di_coarse` | coarse | 7×7 | 49 | 5.19e-08 | true | 6.2s | 0.8s | 7.1s | `output/di_coarse/` |
| `di_medium` | medium | 14×14 | 196 | 0.314 | true | 7.8s | 14.2s | 22.0s | `output/di_medium/` |
| `di_fine` | fine | 21×21 | 441 | 0.373 | true | 8.0s | 22.5s | 30.5s | `output/di_fine/` |
| `di_medium_x2` | medium_x2 | 28×28 | 784 | 0.464 | true | 8.3s | 32.6s | 41.0s | `output/di_medium_x2/` |
| `di_fine_x2` | fine_x2 | 42×42 | 1,764 | 0.861 | true | 8.9s | 25.3s | 34.2s | `output/di_fine_x2/` |

### DoubleIntegrator Multi-Action Variants

| Config | Resolution | Grid | Actions | States | V(s0) | V>0 | Build Time | RVI Time | Total Time | Output |
|--------|-----------|------|---------|--------|-------|-----|------------|----------|------------|--------|
| `di_medium_5act` | medium_5act | 14×14 | 5 | 196 | **0.688** | true | 8.4s | 9.0s | 17.4s | `output/di_medium_5act/` |
| `di_fine_7act` | fine_7act | 21×21 | 7 | 441 | **0.995** | true | 8.1s | 1.6s | 9.7s | `output/di_fine_7act/` |

### Key Observations

- **3-action V values are generally low**: coarse ~0, medium 0.31, fine 0.37. Three discrete actions are insufficient to express effective reach-avoid strategies.
- **coarse V≈0 yet still flagged viable**: V(s0)=5.19e-08 is numerically > 1e-9 threshold, but the strategy is effectively unusable. In practice, coarse is unsuitable as the abstract IMDP.
- **fine_x2 V=0.861 unexpectedly higher than fine**: The denser grid actually improved V — finer partitioning reduces probability interval uncertainty.
- **More actions significantly boost V**: 5-action medium V=0.688 (2.2× improvement), 7-action fine V=0.995 (2.7× improvement). Strategy expressiveness is the bottleneck, not grid resolution.
- **7-action fine RVI converges exceptionally fast**: 1.6s vs 22.5s for same-grid 3-action — the finer action space makes policy iteration converge more easily.

---

## Step 2+3: Pair Analysis Records

### demo — coarse→coarse (49→49, same grid)

| Item | Value |
|------|-------|
| Date | 2026-06-09 |
| Fine IMDP | `output/di_coarse/imdp.pkl` |
| Coarse IMDP | `output/di_coarse/imdp.pkl` |
| f2c Mapping | Strict 1:1 (same grid) |

**ε Binary Search:**

| ε | Feasible | \|R\| | LP Calls | Wall Time |
|---|----------|------|---------|-----------|
| 1.0 | yes | 49 | 1,190 | 0.8s |
| 0.0 | yes | 49 | 1,771 | 12.2s |

**Result:** ε_min = **0.0** (exact simulation)

**RVI + Policy Transfer + MC Validation:**

| Metric | Value |
|--------|-------|
| V_coarse(s0) | 5.19e-08 |
| Empirical Satisfaction | 0.9794 |
| Theoretical Lower Bound | 5.19e-08 |
| Degradation | 0.0 |
| Bound Holds | **True** |
| MC Time | 127.4s |

**Interpretation:** Same grid admits exact simulation (ε=0). MC simulation reaches goal 97.9% of the time, far above the theoretical bound (~0). The real system is highly controllable, but the coarse abstraction is too conservative, underestimating the value.

---

### di_medium_fine — medium→fine (196→441, non-integer ratio 1.5×)

**Status:** Not yet run

---

### di_medium_5act_fine_7act — Recommended Case (196→441, 5act→7act)

**Status:** Completed, but approximate simulation relation does NOT hold.

**Date:** 2026-06-12 ~ 2026-06-14

Detailed analysis in [experiment_5act_vs_7act.md](experiment_5act_vs_7act.md).

| Metric | Value |
|--------|-------|
| ε_min | **0.999** (nearly trivial) |
| Feasible ε range | [0.999, 1.0] |
| \|R_initial\| | 784 pairs |
| \|R\| at ε ≤ 0.998 | **0** (complete collapse) |
| Step 2 Total Time | 182,767s (~50.8h) |
| V_coarse(s0) | 0.6879 |
| Empirical Satisfaction | 1.0000 |
| Theoretical Lower Bound | 0.0000 |
| Degradation | 1.0000 |
| Bound Holds | True (but meaningless) |

**Conclusion:** The action set mismatch (5 vs 7 actions) drives ε → 1. The bound formally holds but degradation=1.0 clamps the theoretical lower bound to 0, providing zero information. Use matching action sets (Option 1 in the experiment doc).

---

## Summary

### All IMDP Builds Overview

```
Name             Grid   Acts  V(s0)    Time    V>0
────             ────   ──    ─────    ────    ───
di_coarse        7×7     3    ~0       7.1s    ✓
di_medium        14×14   3    0.314   22.0s    ✓
di_fine          21×21   3    0.373   30.5s    ✓
di_medium_x2     28×28   3    0.464   41.0s    ✓
di_fine_x2       42×42   3    0.861   34.2s    ✓
di_medium_5act   14×14   5    0.688   17.4s    ✓
di_fine_7act     21×21   7    0.995    9.7s    ✓
```

### Pair Analysis Overview

```
Name                              Coarse→Fine          ε_min   Bound           Status
────                              ───────────          ─────   ─────           ──
demo                              coarse→coarse         0.0     true            ✓ Done
di_medium_5act_fine_7act          medium_5act→fine_7act 0.999   true (trivial)  ✗ Failed
di_medium_fine                    medium→fine             —       —              ○ Pending
```

### Recommended Running Order

```bash
# 1. Quick verification (done)
python run_pipeline.py pair --config configs/approx_sim.yaml demo

# 2. Option 1: Unified 7 actions (next recommended)
#    First build di_medium_7act, then create di_medium_7act → di_fine_7act pair
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution medium_7act \
    --output output/di_medium_7act

# 3. Option 4 verification: integer ratio + same actions
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine_x2

# 4. Non-integer ratio + same actions
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine
```
