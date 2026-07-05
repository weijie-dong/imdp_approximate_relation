# Verification Plan — Colleague-Designed IMDP Approximate Simulation Case

> **Case source**: `doc_en/running_example/new_model.md`
> **Design philosophy**: Model parameters are fixed; the approximate relation emerges naturally through coupling LP relaxation, rather than by modifying model parameters.

---

## 1. Model Definition

### 1.1 Fine IMDP M1 (3 states, p1 has 2 actions)

States: p1=0 (normal), q1=1 (goal), r1=2 (critical). Initial: p1=0.

| State | Action | →q1 | →r1 |
|------|------|-----|-----|
| p1=0 | α=0 | [0.2, 0.7] | [0.1, 0.6] |
| p1=0 | β=1 | [0.1, 0.6] | [0.2, 0.8] |
| q1=1 | α=0 | [1.0, 1.0] | — |
| r1=2 | β=1 | — | [1.0, 1.0] |

Feasible sets (after normalization):
- P(p1,α): t = p(q1) ∈ [0.4, 0.7], p(r1) = 1-t. Corners: **(0.4, 0.6), (0.7, 0.3)**
- P(p1,β): t = p(q1) ∈ [0.2, 0.6], p(r1) = 1-t. Corners: **(0.2, 0.8), (0.6, 0.4)**

### 1.2 Coarse IMDP M2 (3 states, p2 has 2 actions)

States: p2=0 (normal), q2=1 (goal), r2=2 (critical). Initial: p2=0.

| State | Action | →q2 | →r2 |
|------|------|-----|-----|
| p2=0 | γ=0 | [0.1, 0.8] | [0.1, 0.8] |
| p2=0 | δ=1 | [0.1, 0.4] | [0.4, 0.8] |
| q2=1 | γ=0 | [1.0, 1.0] | — |
| r2=2 | δ=1 | — | [1.0, 1.0] |

Feasible sets (after normalization):
- P(p2,γ): t = p(q2) ∈ [0.2, 0.8], p(r2) = 1-t. Corners: **(0.2, 0.8), (0.8, 0.2)**
- P(p2,δ): t = p(q2) ∈ [0.2, 0.4], p(r2) = 1-t. Corners: **(0.2, 0.8), (0.4, 0.6)**

### 1.3 f2c Mapping

f2c_map = [[0], [1], [2]] (1-to-1, all labels match)

Candidate relation: R = {(p1,p2), (q1,q2), (r1,r2)}, init_R automatically includes all 3 pairs.

---

## 2. Competitive Semantics Analysis (Algorithm 2, covered by existing code)

### 2.1 ε = 0 (Exact Simulation) → Does NOT Hold

Check (p1, p2):

**a2 = γ**: a1=α defense successful.
P(p1,α)=[0.4,0.7] ⊆ P(p2,γ)=[0.2,0.8]. Both corners can be exactly matched. ✓

**a2 = δ**: P(p2,δ)=[0.2,0.4] (narrow interval).
- a1=α: P(p1,α)=[0.4,0.7] ⊈ [0.2,0.4]. Corner (0.7,0.3) cannot be matched. ✗
- a1=β: P(p1,β)=[0.2,0.6] ⊈ [0.2,0.4]. Corner (0.6,0.4) cannot be matched. ✗
- **No a1 can defend**. → (p1,p2) **is removed**.

**Conclusion**: ε=0 competitive does NOT hold. |R| = 2 (only (q1,q2), (r1,r2)).

### 2.2 ε = 0.2 (Approximate Simulation) → Holds

Requires W(R) ≥ 1-ε = 0.8.

Check (p1, p2), a2 = δ:

a1=β can defend:
- Corner (0.2, 0.8): Take μ2=(0.2,0.8)∈P(p2,δ), exact coupling, W(R)=1.0 ≥ 0.8. ✓
- Corner (0.6, 0.4): Take μ2=(0.4,0.6)∈P(p2,δ) (upper-bound corner of δ):
  - W(q1,q2)=0.4, W(q1,r2)=0.2, W(r1,q2)=0, W(r1,r2)=0.4
  - W(R) = 0.4+0.4 = **0.8 = 1-ε**. ✓ (Exactly at the threshold!)

a2=γ: a1=α defends (same as ε=0). ✓

**Conclusion**: ε=0.2 competitive holds. All 3 pairs survive.

### 2.3 ε_min Prediction

- ε=0: Does NOT hold ((p1,p2) removed)
- ε=0.2: Holds ((p1,p2) survives)
- Bottleneck: (p1,p2) vs a2=δ, corner (0.6,0.4) maximum coupling = 0.8 = 1-0.2
- **ε_min = 0.2**

---

## 3. Verification Scenario Summary

| Experiment | ε | Expected (p1,p2) | Expected \|R\| | What It Tests |
|------|---|-------------|-----------|---------|
| A | 0 | ✗ removed | 2 | pre-filter + corner_failed path |
| B | 0.2 | ✓ survives | 3 | knife-edge coupling (exactly 0.8) |
| C | ε_min | — | — | binary search finds ≈ 0.2 |

**Additional verification**:
- D: lazy vs corner cross-validation (ε=0, ε=0.2, ε=ε_min)
- E: direct coupling check (manually call check_coupling_lazy on (p1,p2))

---

## 4. Implementation Plan

### Task 1: Create `verify_toy_example.py`

Fully reuse `build_toy_imdp` from `verify_paper_examples.py`.

```python
import numpy as np
from verify_paper_examples import build_toy_imdp
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.lazy_enum import check_coupling_lazy
from core.approx_sim.corners import enumerate_corners, get_successor_info

def build_M1():
    """Fine IMDP: 3 states. p1 has 2 actions (α,β), q1/r1 absorbing."""
    P_full = [
        [np.array([[0.2, 0.7], [0.1, 0.6]]),    # p1, α → q1, r1
         np.array([[0.1, 0.6], [0.2, 0.8]])],   # p1, β → q1, r1
        [np.array([[1.0, 1.0]])],                 # q1, α → q1
        [np.array([[1.0, 1.0]])],                 # r1, β → r1
    ]
    S_id = [
        [np.array([1, 2]), np.array([1, 2])],
        [np.array([1])],
        [np.array([2])],
    ]
    goal = [False, True, False]
    crit = [False, False, True]
    return build_toy_imdp(P_full, S_id,
                          [np.array([0.0]), np.array([1.0])],
                          goal, crit, s_init=0)

def build_M2():
    """Coarse IMDP: 3 states. p2 has 2 actions (γ,δ), q2/r2 absorbing."""
    P_full = [
        [np.array([[0.1, 0.8], [0.1, 0.8]]),     # p2, γ → q2, r2
         np.array([[0.1, 0.4], [0.4, 0.8]])],    # p2, δ → q2, r2
        [np.array([[1.0, 1.0]])],                 # q2, γ → q2
        [np.array([[1.0, 1.0]])],                 # r2, δ → r2
    ]
    S_id = [
        [np.array([1, 2]), np.array([1, 2])],
        [np.array([1])],
        [np.array([2])],
    ]
    goal = [False, True, False]
    crit = [False, False, True]
    return build_toy_imdp(P_full, S_id,
                          [np.array([0.0]), np.array([1.0])],
                          goal, crit, s_init=0)
```

### Task 2: Run Verification

1. **Experiment A**: `compute_min_epsilon(method='lazy')` → ε_min ≈ 0.2
2. **Experiment B**: `compute_min_epsilon(method='corner')` → ε_min ≈ 0.2 (cross-validation)
3. **Experiment C**: Directly call `check_coupling_lazy` on (p1,p2) to verify:
   - ε=0: corner_failed when a2=δ (corner (0.6,0.4) fails)
   - ε=0.2: all corners pass, W(R)=0.8 for corner (0.6,0.4)

### Task 3: Record Results

`doc_en/running_example/verification_record.md`

---

## 5. Files

| File | Action |
|------|------|
| `verify_toy_example.py` | **Create** |
| `doc_en/running_example/verification_record.md` | **Create** |

Do not modify any files under `core/`. Reuse `build_toy_imdp` from `verify_paper_examples.py`.

---

## 6. Verification Checklist

1. ε_min(lazy) ≈ ε_min(corner) ≈ 0.2
2. At ε=0, (p1,p2) is removed, |R|=2
3. At ε=0.2, (p1,p2) survives, |R|=3
4. No lazy convergence warnings
5. a2=δ must be defended by a1=β (not α) — verify correct action selection
6. Corner (0.6,0.4) vs P(p2,δ) coupling mass exactly = 0.8 — numerical precision test
