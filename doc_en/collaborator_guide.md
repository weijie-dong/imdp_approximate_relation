# Collaborator Quick Start

> ⚠️ **Update (2026-07)**: `method='lazy'` is deprecated (unsound). Use `method='corner'` (exact) or
> `method='tiered'` (sound acceleration). See [`UPDATE_lazy_to_tiered_EN.md`](UPDATE_lazy_to_tiered_EN.md).
> The environment / pipeline / file-manifest parts of this guide are still valid; only the method
> choice changed. Full doc index: [`README_EN.md`](README_EN.md).

## 1. Get the Code

```bash
git clone <this-repo-url>
cd imdp-synthesis
```

## 2. Install Dependencies

```bash
conda create -n dyabstract python=3.13
conda activate dyabstract
pip install -r requirements.txt
pip install jax cvxpy pyyaml
```

> Storm is optional. It only needs `stormpy` if you plan to use `--solver storm`.

## 3. Verify the Original Functionality

```bash
python Main_IMDP.py --model Test1D --solver jax
```

## 4. Smoke Test the New Feature

```bash
python test_approx_sim_synthetic.py
```

Takes ~20 seconds. Should print `Bound holds: True`.

## 5. Run the Demo Pipeline

```bash
python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

Demo uses `coarse→coarse` (same 7×7 grid, 49→49 states). Expected result: ε_min = 0.0 (exact simulation), ~150 seconds.

## 6. Run a Real Case

```bash
# Build two IMDPs at different resolutions
python run_pipeline.py build --config configs/approx_sim.yaml di_medium
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# Run the full pair analysis (ε search + policy transfer + MC validation)
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine
```

## What Just Happened

| Step | What it does | Output |
|------|-------------|--------|
| `build` | Builds one IMDP + checks V(s0) > 0 | `output/.../imdp.pkl` + `params.yaml` |
| `pair` (Step 2) | ε binary search via Algorithm 2 | `output/.../eps.pkl` |
| `pair` (Step 3) | Policy transfer + Monte Carlo validation | `output/.../results.pkl` |

## Where to Go Next

- [step_workflow.md](step_workflow.md) — Full walkthrough with every command explained
- [log.md](log.md) — All past run results and recommended next experiments
- [migration_guide.md](migration_guide.md) — File manifest (what was added to the original project)

## Available Models

```bash
# List all predefined build/pair configs
python run_pipeline.py --config configs/approx_sim.yaml --list
```
