# IMDP 近似关系计算：性能瓶颈分析与优化方案

> 本文档详细分析 Algorithm 2（竞争性 ε-近似仿真关系计算）的计算瓶颈，评估嵌套 LP 对偶方法（Dual LP）并被实验证伪，最后梳理可行的优化方向。

> **重要更新（2026-06-28）**：嵌套 LP 对偶方法已通过实验和数学分析被证伪。详见 `dual_lp_implementation_plan.md` 第 3 节。

---

## 1. 计算瓶颈详细分析

### 1.1 算法结构

Algorithm 2 计算两个 IMDP 之间的最大竞争性 ε-近似仿真关系 R ⊆ S_fine × S_coarse。其核心是一个固定点迭代（外层循环），每次迭代对所有当前 R 中的 (s1, s2) 对执行嵌套检查：

```
Algorithm 2: 竞争性近似关系计算
──────────────────────────────────────
 1  R ← {(x1, x2) : L1(x1) = L2(x2)}      // 初始化：所有标签一致的对
 2  repeat
 3      R' ← R
 4      forall (x1, x2) ∈ R' do             // 遍历所有关系对
 5          valid ← True
 6          forall a2 ∈ A2 s.t. valid do     // ∀ coarse action
 7              found ← False
 8              forall a1 ∈ A1 s.t. ¬found do // ∃ fine action
 9                  ok ← True
10                  forall c1 ∈ C(x1, a1) s.t. ok do  // ∀ fine corners
11                      feas ← CouplingLP(x1, a1, x2, a2, c1)
12                      if ¬feas then ok ← False
13                  if ok then found ← True
14              if ¬found then valid ← False
15          if ¬valid then R ← R \ {(x1, x2)}
16  until R = R'
17  return R
```

### 1.2 复杂度分解

总复杂度为：

```
O( |X1|² · |X2|² · |A1| · |A2| · max|C(x,a)| · LP(|X1|·|X2|) )
```

各因子含义：

| 因子 | 含义 | 典型值（196→441 实验） |
|------|------|----------------------|
| \|X1\|²·\|X2\|² | 固定点迭代 × 关系对 | 最多 784 对（几何剪枝后） |
| \|A1\|·\|A2\| | 动作对 | 5 × 7 = 35 |
| max\|C(x,a)\| | Fine 角点数量 | **2^(k1-1)，k1≈13 → ~4096** |
| LP(\|X1\|·\|X2\|) | 单次 LP 求解 | 变量 k1·k2+L ≈ 200，~20ms |

### 1.3 各阶段耗时分布（实测数据）

基于 di_medium_5act → di_fine_7act 实验（196→441 states，耗时 50.8 小时）：

| 组件 | 耗时占比 | 说明 |
|------|---------|------|
| **LP 求解** | **~95%** | CVXPY + ECOS/SCS，每次 ~20ms |
| 角点枚举 | ~4% | 三种策略：greedy / HalfspaceIntersection / LP-based |
| Pre-filter + 其他 | ~1% | 快速必要性条件检查 |

### 1.4 瓶颈根源：角点数量的指数增长

Fine IMDP 的概率多面体 P(x1, a1) 是区间约束单纯形：

```
P(x1, a1) = { p ∈ R^k1 : Σp_i = 1, l_i ≤ p_i ≤ u_i ∀i }
```

根据 Minkowski-Weyl 定理，检查「∀p ∈ P1, coupling feasible」等价于检查「∀c1 ∈ C(P1), coupling feasible」，其中 C(P1) 是多面体的顶点集（角点）。角点数量随 k1（后继状态数）指数增长：

| k1 | 角点数量 ≈ 2^(k1-1) |
|----|---------------------|
| 8  | 128 |
| 10 | 512 |
| 12 | 2,048 |
| 13 | 4,096 |
| 16 | 32,768 |
| 20 | 524,288 |

对于 k1=13（典型值），每个 (a1,a2) 对需要求解 ~4096 次 LP。在 196→441 实验中，每次 epsilon 迭代有 784 对 × 35 动作组合 = 27,440 个四元组，如果不加 pre-filter，理论上需要 27,440 × 4,096 ≈ 1.12 亿次 LP 调用。

### 1.5 为什么角点枚举是必要的（竞争性语义）

竞争性语义的条件是：

$$\forall a_2 \in A_2, \exists a_1 \in A_1: \forall \mu_1 \in \mathcal{P}(x_1, a_1), \exists \mu_2 \in \mathcal{P}(x_2, a_2): (\mu_1, \mu_2) \in \overline{\mathcal{R}}_\varepsilon$$

即：对 coarse 系统的**每一个**动作，fine 系统必须存在一个**单一**的防御动作，该动作能应对 fine 概率多面体中的**所有**可能分布。

定义 $\mathcal{S}_{a_2}$ 为可以被 ε-耦合到 coarse 系统（使用 a₂）的所有 fine 分布的集合。条件等价于：

$$\mathcal{P}(x_1, a_1) \subseteq \mathcal{S}_{a_2}$$

这是一个**凸多面体包含**问题。由于 $\mathcal{P}(x_1, a_1)$ 是一个凸多面体，而 $\mathcal{S}_{a_2}$ 也是凸集，根据 Minkowski-Weyl 定理，包含关系等价于检查所有生成元（角点）。这就是 Algorithm 2 第 10 行 `forall c1 ∈ C(x1, a1)` 的几何根源。

---

## 2. 嵌套 LP 对偶方法（Dual LP）—— 已证伪 ⚠️

> **状态**：此方法已被实验和数学分析证伪。本节保留推导过程和错误分析，供参考。

### 2.1 方案概要

`coupling_dual.py` 中的嵌套 LP 对偶方法尝试将 O(2^k1) 次 per-corner LP 调用替换为 1 次 LP。推导见于 `interval_coupling_dual.md`。

核心思路：
1. 耦合 LP 的对偶：M(p) = min_{α,γ,τ} pᵀα + τ
2. 嵌套求 min：min_{p∈P₁} M(p) = min_{α,γ,τ} [τ + min_{p∈P₁} pᵀα]
3. 内层 LP 再对偶：min_{p∈P₁} pᵀα = max_{μ,ν,λ} lᵀμ - uᵀν + λ
4. 合并为单一 LP

（完整推导见 `interval_coupling_dual.md` 和本文件的历史版本）

### 2.2 实验证伪

在 Test1D 模型（5-state × 15-state）上进行逐对对比（`debug_dual.py`）：

- **6,345 次 per-corner LP vs 405 次 dual LP**
- **150 次不一致，全部为 dual LP 假阴性**
- Dual LP 返回 `status: unbounded`，最优值为 `-∞`

典型案例深层分析：
```
(s1=0, s2=0, a1=0, a2=0, eps=0.5)
  Fine: P_upper = [0.0478, 0.0477, 0.9044, 0.9044]  ← Σ = 1.9043 > 1
  Per-corner: 12/12 corners PASS
  Dual LP:    status=unbounded, opt_val=-inf, feasible=False  ← 假阴性
```

### 2.3 数学错误定位

推导 Step 3-5 中的关键变换：

$$\min_{\alpha,\gamma,\tau} \Bigl[\tau + \max_{\mu,\nu,\lambda: \mu-\nu+\lambda\mathbf{1}=\alpha} \bigl(l^T\mu - u^T\nu + \lambda\bigr)\Bigr]$$

被错误地改写为：

$$\min_{\mu,\nu,\lambda,\gamma,\tau} \; l^T\mu - u^T\nu + \lambda + \tau \quad \text{s.t. } \alpha = \mu-\nu+\lambda\mathbf{1} \text{ and coupling dual constraints}$$

这个变换**不等价**——它将 "min-max" 问题强行变为 "min-min" 问题。一般地：

$$\min_x \max_y f(x,y) \neq \min_{x,y} f(x,y)$$

### 2.4 为什么会导致 unbounded

当 Σ P_upper > 1（IMDP 数据的常态——区间上界之和通常超过 1），嵌套 LP 存在使目标 → -∞ 的方向：

设 ν_i = M → ∞，λ = -2M：
- 约束迫使 γ_min ≥ 3M，γ_j ≥ 3M，δ ≥ 3M
- 目标 ≈ -(Σ P_upper)·M + (-2M) + 3M = (1 - Σ P_upper)·M → **-∞**

因为 min 驱动 ν → ∞（通过 `-u^T ν` 项），而原问题中的 max 会阻止这种发散。

### 2.5 结论

嵌套 LP 对偶方法在数学上不等价于原始 per-corner LP 检查，产生大量假阴性。该方法不能用于 Algorithm 2。

角点枚举的几何必要性（Minkowski-Weyl 定理）无法通过对偶技巧绕过，这与 `Competitive_Approximate_Relation_Computation.md` Section 3 的结论一致。

详细分析见：`dual_lp_implementation_plan.md` 第 3 节。

---

## 4. 其他优化方向

以下方法可以进一步加速计算，按优先级排列。

### 4.1 商业 LP 求解器（低投入，高回报）

**现状**：CVXPY 默认使用开源求解器 ECOS/OSQP/SCS。

**改进**：改用 Gurobi 或 Mosek（均提供免费学术许可证）。

**预期加速**：10-50x。商业求解器的 Simplex/Barrier 方法针对中小规模 LP 高度优化。

**实现**：在 `check_coupling_dual` 中添加 `solver` 参数：
```python
prob.solve(verbose=False, solver='GUROBI')
```

### 4.2 Direct μ₂ Variableization（消除 Coarse 角点枚举）

**现状**：耦合 LP 中，coarse marginal 表示为 coarse corner 的凸组合 `Σ_l β[l] · V2[l][j]`，需要枚举 coarse 角点。

**改进**：将 μ₂ 直接作为变量，加上区间约束：
```
μ₂[j] 直接作为变量，约束为：
P2_lower[j] ≤ μ₂[j] ≤ P2_upper[j]
Σ_j μ₂[j] = 1
```

**效果**：消除 L 个 coarse 角点枚举，将 coarse 约束从 L 个（可能指数级）降低为 2k₂ 个。

### 4.3 Action 排序启发式（极低投入）

**现状**：`algorithm.py` 中 `_check_pair` 按任意顺序遍历 a1。

**改进**：按 action value 与 a2 的接近程度排序 a1，优先尝试最可能成功的 fine action。如果更早找到 defending action，可提前退出内层循环。

### 4.4 Pre-filter 强化

**现状**：仅有 fine 侧的 pre-filter（检查 P1_lower 的未覆盖质量）。

**改进**：
- 添加 coarse 侧对称检查
- 快速二分图匹配估计（比 LP 便宜但比 pre-filter 更精确）

### 4.5 多 CPU 并行改进

**现状**：使用 `ThreadPoolExecutor`（因为 CVXPY 底层 C 求解器释放 GIL）。

**改进**：
- 预计算所有 corner 数据（pl, pu），避免线程内 lazy cache 的 Lock 争用
- 对于 Dual LP 场景（每次 LP 求解 <5ms），改用批量提交减少线程调度开销
- 考虑 `ProcessPoolExecutor`（如果 Python 层开销成为瓶颈）

### 4.6 LP Warm-Starting（中期）

**现状**：每次固定点迭代独立求解 Dual LP。

**改进**：存储上一轮迭代的最优对偶变量值，作为下一轮迭代的 warm start 传入求解器。由于 R 在迭代间单调缩小（约束减少），上一轮的解仍然（接近）可行。

**依赖**：需要 Gurobi/Mosek（开源求解器 warm start 支持有限）。

### 4.7 Lazy Corner Enumeration（Cutting-Plane，备用方案）

如果 Dual LP 在极端情况下出现数值问题，可采用 Lazy Corner Enumeration 作为 fallback：

1. 从一个小的角点子集开始
2. 检查所有当前角点是否通过耦合 LP
3. 如果都通过，求解分离问题：找最违反的角点（或证明不存在）
4. 如果找到违反角点，加入子集并重复

**分离子问题**：利用耦合 LP 的对偶变量构造一个在 P₁ 上最小化的 LP，其最优解即为最违反的角点。

### 4.8 GPU 批量 LP 求解（长期探索）

**思路**：将多个独立的小 LP 批量放到 GPU 上求解：
- 方案 A：使用 NVIDIA cuOpt 批量求解 LP
- 方案 B：在 JAX 中实现简单的 primal-dual 内点法（利用现有 JAX GPU 能力）

**挑战**：GPU LP 求解器成熟度不及 CPU，float32 精度可能影响正确性。

---

## 5. 实施建议

### 推荐实施顺序

| 阶段 | 内容 | 投入 | 预期加速 |
|------|------|------|---------|
| **Phase 1** | 商业求解器 + Pre-filter 强化 + Action 排序 | 低 | **10-50x** |
| **Phase 2** | 并行改进 + Warm-start | 低-中 | 2-10x |
| **Phase 3** | Lazy Corner Enumeration | 中-高 | 2-10x |
| **Phase 4** | GPU 批量 LP | 高 | 探索性 |

### 修改文件清单（Phase 1）

| 文件 | 修改内容 |
|------|---------|
| `core/approx_sim/coupling.py` | 添加 `solver` 参数，传至 `prob.solve()` |
| `core/approx_sim/algorithm.py` | 添加 Action 排序启发式、并行改进 |
| `core/options.py` | 添加 `--lp_solver` 参数 |
| `time_algorithm2.py` | 传递 `--lp_solver` 参数 |

---

## 参考文献

- Badings, T. et al. "Robust Control for Dynamical Systems with Uncertainty via Interval Markov Decision Processes." CDC 2025 / JAIR 2023.
- Hashemi, V. et al. "Polynomial-time alternating probabilistic bisimulation for interval MDPs." SETTA, 2017.
- Ben-Tal, A. & Nemirovski, A. *Robust Optimization*. Princeton University Press, 2009. (嵌套 LP 对偶的标准技术)
- Rockafellar, R.T. *Convex Analysis*. Princeton University Press, 1997. (Minkowski-Weyl 定理)
