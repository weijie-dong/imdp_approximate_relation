# Verification Plan — 同事设计的 IMDP 近似模拟案例

> **案例来源**: `doc_en/running_example/new_model.md`
> **设计理念**: 模型参数固定，近似关系通过耦合 LP 的松弛自然涌现，而非修改模型参数。

---

## 1. 模型定义

### 1.1 Fine IMDP M1（3 状态，p1 有 2 action）

状态: p1=0(normal), q1=1(goal), r1=2(critical)。初始: p1=0。

| 状态 | 动作 | →q1 | →r1 |
|------|------|-----|-----|
| p1=0 | α=0 | [0.2, 0.7] | [0.1, 0.6] |
| p1=0 | β=1 | [0.1, 0.6] | [0.2, 0.8] |
| q1=1 | α=0 | [1.0, 1.0] | — |
| r1=2 | β=1 | — | [1.0, 1.0] |

Feasible sets（归一化后）:
- P(p1,α): t = p(q1) ∈ [0.4, 0.7], p(r1) = 1-t。Corners: **(0.4, 0.6), (0.7, 0.3)**
- P(p1,β): t = p(q1) ∈ [0.2, 0.6], p(r1) = 1-t。Corners: **(0.2, 0.8), (0.6, 0.4)**

### 1.2 Coarse IMDP M2（3 状态，p2 有 2 action）

状态: p2=0(normal), q2=1(goal), r2=2(critical)。初始: p2=0。

| 状态 | 动作 | →q2 | →r2 |
|------|------|-----|-----|
| p2=0 | γ=0 | [0.1, 0.8] | [0.1, 0.8] |
| p2=0 | δ=1 | [0.1, 0.4] | [0.4, 0.8] |
| q2=1 | γ=0 | [1.0, 1.0] | — |
| r2=2 | δ=1 | — | [1.0, 1.0] |

Feasible sets（归一化后）:
- P(p2,γ): t = p(q2) ∈ [0.2, 0.8], p(r2) = 1-t。Corners: **(0.2, 0.8), (0.8, 0.2)**
- P(p2,δ): t = p(q2) ∈ [0.2, 0.4], p(r2) = 1-t。Corners: **(0.2, 0.8), (0.4, 0.6)**

### 1.3 f2c 映射

f2c_map = [[0], [1], [2]]（1-to-1，全部标签匹配）

候选关系: R = {(p1,p2), (q1,q2), (r1,r2)}，init_R 自动包含全部 3 对。

---

## 2. Competitive 语义分析（Algorithm 2，现有代码覆盖）

### 2.1 ε = 0（精确模拟）→ 不成立

检查 (p1, p2):

**a2 = γ**: a1=α 防御成功。
P(p1,α)=[0.4,0.7] ⊆ P(p2,γ)=[0.2,0.8]。两个 corner 均可精确匹配。✓

**a2 = δ**: P(p2,δ)=[0.2,0.4]（窄区间）。
- a1=α: P(p1,α)=[0.4,0.7] ⊈ [0.2,0.4]。Corner (0.7,0.3) 无法匹配。✗
- a1=β: P(p1,β)=[0.2,0.6] ⊈ [0.2,0.4]。Corner (0.6,0.4) 无法匹配。✗
- **无 a1 能防御**。→ (p1,p2) **被移除**。

**结论**: ε=0 competitive 不成立。|R| = 2（仅 (q1,q2), (r1,r2)）。

### 2.2 ε = 0.2（近似模拟）→ 成立

要求 W(R) ≥ 1-ε = 0.8。

检查 (p1, p2)，a2 = δ：

a1=β 可防御:
- Corner (0.2, 0.8): 取 μ2=(0.2,0.8)∈P(p2,δ)，精确耦合，W(R)=1.0 ≥ 0.8。✓
- Corner (0.6, 0.4): 取 μ2=(0.4,0.6)∈P(p2,δ)（δ 的上界 corner）:
  - W(q1,q2)=0.4, W(q1,r2)=0.2, W(r1,q2)=0, W(r1,r2)=0.4
  - W(R) = 0.4+0.4 = **0.8 = 1-ε**。✓（恰好达到阈值！）

a2=γ: a1=α 防御（同 ε=0）。✓

**结论**: ε=0.2 competitive 成立。所有 3 对存活。

### 2.3 ε_min 预测

- ε=0: 不成立（(p1,p2) 移除）
- ε=0.2: 成立（(p1,p2) 存活）
- 瓶颈: (p1,p2) 对 a2=δ，corner (0.6,0.4) 的耦合最大为 0.8 = 1-0.2
- **ε_min = 0.2**

---

## 3. 验证场景总结

| 实验 | ε | 预期 (p1,p2) | 预期 \|R\| | 测试什么 |
|------|---|-------------|-----------|---------|
| A | 0 | ✗ 移除 | 2 | pre-filter + corner_failed 路径 |
| B | 0.2 | ✓ 存活 | 3 | knife-edge 耦合（恰好 0.8） |
| C | ε_min | — | — | binary search 找到 ≈ 0.2 |

**额外验证**:
- D: lazy vs corner 交叉验证（ε=0, ε=0.2, ε=ε_min）
- E: 直接耦合检查（对 (p1,p2) 手动调用 check_coupling_lazy）

---

## 4. 实施计划

### Task 1: 创建 `verify_toy_example.py`

完全复用 `verify_paper_examples.py` 中的 `build_toy_imdp`。

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

### Task 2: 运行验证

1. **Experiment A**: `compute_min_epsilon(method='lazy')` → ε_min ≈ 0.2
2. **Experiment B**: `compute_min_epsilon(method='corner')` → ε_min ≈ 0.2（交叉验证）
3. **Experiment C**: 直接对 (p1,p2) 调用 `check_coupling_lazy` 验证:
   - ε=0: a2=δ 时 corner_failed（corner (0.6,0.4) 失败）
   - ε=0.2: all corners pass, W(R)=0.8 for corner (0.6,0.4)

### Task 3: 记录结果

`doc_en/running_example/verification_record.md`

---

## 5. 文件

| 文件 | 动作 |
|------|------|
| `verify_toy_example.py` | **新建** |
| `doc_en/running_example/verification_record.md` | **新建** |

不修改任何 `core/` 下文件。复用 `verify_paper_examples.py` 中的 `build_toy_imdp`。

---

## 6. 验证检查清单

1. ε_min(lazy) ≈ ε_min(corner) ≈ 0.2
2. ε=0 时 (p1,p2) 被移除，|R|=2
3. ε=0.2 时 (p1,p2) 存活，|R|=3
4. 无 lazy 收敛警告
5. a2=δ 必须由 a1=β（非 α）防御 — 验证 action 选择正确
6. Corner (0.6,0.4) vs P(p2,δ) 的耦合质量恰好 = 0.8 — 数值精度测试
