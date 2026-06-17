# Approximate Simulation Feature Migration Guide

This document describes how to port the IMDP approximate simulation feature to a fresh clone of the original project on another machine using a minimal file set.

## Prerequisites

A clone of the original IMDP synthesis open-source project on the target machine:

```bash
git clone <original-repo-url>
cd imdp-synthesis
```

## Step 1: Base Environment Setup

```bash
conda create -n dyabstract python=3.13
conda activate dyabstract
pip install -r requirements.txt
```

Verify that the original functionality works (optional):

```bash
python Main_IMDP.py --model Test1D --solver jax
```

## Step 2: Additional Dependencies

```bash
pip install cvxpy pyyaml
```

- `cvxpy`: Coupling LP solver (core of Algorithm 2)
- `pyyaml`: YAML config file parsing

## Step 3: Port Files

Copy all files below from the source machine to the target machine at the corresponding locations. Use the **latest working-copy versions** (some files may contain uncommitted changes), not git committed versions.

### 3.1 Create Directories

Create the following empty directories under the project root:

```bash
mkdir -p core/approx_sim
mkdir -p steps
mkdir -p configs
```

### 3.2 Core Algorithm Module (Required)

Copy the following files to `core/approx_sim/`:

| File | Purpose |
|------|---------|
| `core/approx_sim/__init__.py` | Package initialization |
| `core/approx_sim/algorithm.py` | Algorithm 2 fixed-point iteration (core algorithm, **use working-copy version**) |
| `core/approx_sim/corners.py` | Transition polytope corner enumeration |
| `core/approx_sim/coupling.py` | Coupling LP construction and solving |
| `core/approx_sim/epsilon_search.py` | ε binary search (**use working-copy version**) |
| `core/approx_sim/mapping.py` | Fine-to-coarse state mapping (**use working-copy version**) |
| `core/approx_sim/policy_transfer.py` | Policy transfer from coarse to fine IMDP |

### 3.3 Benchmark Models (Required)

Copy the following files to `benchmarks/`:

| File | Purpose |
|------|---------|
| `benchmarks/DoubleIntegrator_approx_sim.py` | Double integrator model (primary test model, **use working-copy version**) |
| `benchmarks/Dubins3D_approx_sim.py` | Dubins3D model |

### 3.4 Modify Existing Files (Required)

The target machine already has `benchmarks/__init__.py`. Two manual edits are needed.

**Edit 1** — Add two import lines near the top of the file:

```python
from benchmarks.Dubins3D_approx_sim import Dubins3DApproxSim
from benchmarks.DoubleIntegrator_approx_sim import DoubleIntegratorApproxSim
```

**Edit 2** — Add two entries to the `model_map` dictionary at the end of the `create_model()` function. Locate the structure resembling:

```python
model_map = {
    "Test1D": Test1D,
    "Pendulum": Pendulum,
    # ... more existing models ...
}
```

And add:

```python
    "DoubleIntegratorApproxSim": DoubleIntegratorApproxSim,
    "Dubins3DApproxSim": Dubins3DApproxSim,
```

### 3.5 Pipeline Scripts (Recommended)

Copy the following files to `steps/`:

| File | Purpose |
|------|---------|
| `steps/step1_build_imdp.py` | Step 1: Build IMDP + V>0 check |

Copy the following files to `configs/`:

| File | Purpose |
|------|---------|
| `configs/approx_sim.yaml` | Build / pair YAML configuration |

Copy the following files to the project root:

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Main entry point, supports `build` and `pair` subcommands |
| `steps/step2_epsilon_search.py` | Step 2: ε binary search |
| `steps/step3_validate.py` | Step 3: Policy transfer + RVI + MC validation |

### 3.6 Optional Files

| File | Location | Notes |
|------|----------|-------|
| `test_approx_sim_synthetic.py` | Project root | Small-scale synthetic test (5→15 states, ~20s) |
| `time_algorithm2.py` | Project root | Algorithm 2 timing measurement |
| `Main_ApproxSim.py` | Project root | Alternative CLI entry point |
| `core/approx_sim/coupling_dual.py` | `core/approx_sim/` | LP dual formulation (experimental) |

## Step 4: Verification

### 4.1 Smoke Test

```bash
python test_approx_sim_synthetic.py
```

Should complete in about 20 seconds, output pass/fail.

### 4.2 Build a Single IMDP

```bash
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution coarse \
    --output output/di_coarse
```

Should output V(s0) value and build time, generate `output/di_coarse/imdp.pkl`.

### 4.3 Full Demo Pipeline

```bash
python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

Demo uses coarse→coarse (same grid 49→49), expected ε_min = 0.0 (exact simulation), ~150 seconds to complete.

### 4.4 Further Verification

```bash
# Build medium + fine and run pair
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution medium \
    --output output/di_medium

python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution fine \
    --output output/di_fine

python steps/step2_epsilon_search.py \
    --imdp_coarse output/di_medium/imdp.pkl \
    --imdp_fine output/di_fine/imdp.pkl \
    --output output/di_medium_fine

python steps/step3_validate.py \
    --imdp_coarse output/di_medium/imdp.pkl \
    --imdp_fine output/di_fine/imdp.pkl \
    --eps output/di_medium_fine/eps.pkl \
    --output output/di_medium_fine
```

## File Manifest Summary

After porting, files added/modified on the target machine:

```
imdp-synthesis/
├── configs/
│   └── approx_sim.yaml                    # Added
├── core/
│   └── approx_sim/                        # Added directory
│       ├── __init__.py
│       ├── algorithm.py
│       ├── corners.py
│       ├── coupling.py
│       ├── coupling_dual.py               # Optional
│       ├── epsilon_search.py
│       ├── mapping.py
│       └── policy_transfer.py
├── benchmarks/
│   ├── __init__.py                        # Modified (added 2 model registrations)
│   ├── DoubleIntegrator_approx_sim.py     # Added
│   └── Dubins3D_approx_sim.py             # Added
├── steps/                                 # Added directory
│   ├── step1_build_imdp.py
│   ├── step2_epsilon_search.py
│   └── step3_validate.py
├── run_pipeline.py                        # Added
├── Main_ApproxSim.py                      # Optional
├── test_approx_sim_synthetic.py           # Optional
└── time_algorithm2.py                     # Optional
```

**Total: 13 required files + 5 optional files, 1 existing file modified.**
