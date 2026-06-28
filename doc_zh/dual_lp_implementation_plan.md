# Dual LP 方案：探索、实验与证伪

> 本文档记录了将 `coupling_dual.py` 中的嵌套 LP 对偶方法集成到 Algorithm 2 主路径的完整过程，包括初始方案设计、代码实现、实验对比，以及最终的数学证伪。

---

## 1. 初始动机

### 1.1 性能瓶颈

Algorithm 2 的核心瓶颈在 `algorithm.py:179-194`：每个 `(s1,s2,a1,a2)` 四元组需要遍历 fine IMDP 概率多面体的所有角点（corner vertices），每个角点调用一次 `check_coupling()` LP。角点数量按 `2^(k1-1)` 指数增长（k1 = 后继状态数）。

在 196→441 状态的实验中，每次 epsilon 迭代需要解数十万次 LP，总耗时 ~50.8 小时，其中 LP 求解占 ~95%。

### 1.2 Dual LP 方案

`coupling_dual.py` 实现了嵌套 LP 对偶方法，声称可以将 O(2^k1) 次 LP 调用替换为 1 次 LP。推导见于 `doc_en/interval_coupling_dual.md`。核心思路：

1. 耦合 LP 的对偶：M(p) = min_{α,γ,τ} pᵀα + τ
2. 嵌套求 min：min_{p∈P₁} M(p) = min_{α,γ,τ} [τ + min_{p∈P₁} pᵀα]
3. 内层 LP 再对偶：将 min_{p∈P₁} pᵀα 表示为 max_{μ,ν,λ} lᵀμ - uᵀν + λ
4. 合并为单一 LP

如果正确，这将使 k1=13 时 ~4096 次 LP 调用降至 1 次（~4000x 加速）。

---

## 2. 代码实现

为了便于对比两种方案的效果，在 Algorithm 2 中通过 `method` 参数提供切换接口（详见第 4 节"保留的代码修改"）。

---

## 3. 实验测试与证伪

### 3.1 实验设置

**测试案例**：Test1D 模型，5-state coarse × 15-state fine，3 个 epsilon 值（1.0, 0.5, 0.0）

**对比方法**：对每个 `(s1,s2,a1,a2)` 四元组，同时运行 per-corner LP 和 dual LP，比较 feasibility 结果。

**脚本**：`debug_dual.py`（逐对对比，打印详细数值）

### 3.2 实验结果

```
Total corner LPs: 6345
Total dual LPs:   405
Disagreements:    150    ← dual LP 与 corner LP 结果不一致的次数
```

**150 个不一致全部是假阴性**——dual LP 判定 infeasible，但所有 corner LP 均判定 feasible。

### 3.3 典型案例 Deep Dive

```
(s1=0, s2=0, a1=0, a2=0, eps=0.5)

Fine: k1=4, P_lower=[0.0001 0.0001 0.0477 0.0478]
              P_upper=[0.0478 0.0477 0.9044 0.9044]
Coarse: k2=2, L=2
R_local: |R|=4 pairs

Per-corner LP: 12/12 corners PASS  ✓
Dual LP:
    status:     unbounded      ← 无下界！
    opt_val:    -inf
    feasible:   False          ← 假阴性

*** BUG CONFIRMED: dual LP false negative ***
```

关键数据：`P_upper` 的总和 = 0.0478 + 0.0477 + 0.9044 + 0.9044 = **1.9043 > 1**。这是 IMDP 概率区间数据的常态——各维度的上界之和可以（且通常）超过 1。

### 3.4 数学证伪

#### 3.4.1 错误定位

`interval_coupling_dual.md` 推导的关键步骤（Step 3）：

$$\min_{p \in P_1} M(p) = \min_{\alpha,\gamma,\tau} \Bigl[\tau + \min_{p \in P_1} p^T\alpha\Bigr]$$

然后对 `min_{p∈P₁} pᵀα` 应用 LP 对偶（Step 4）：

$$\min_{p \in P_1} p^T\alpha = \max_{\mu \geq 0, \nu \geq 0, \lambda}\; l^T\mu - u^T\nu + \lambda \quad \text{s.t. } \mu - \nu + \lambda\mathbf{1} = \alpha$$

代入外层得到（Step 5）：

$$\min_{\alpha,\gamma,\tau} \Bigl[\tau + \max_{\mu,\nu,\lambda: \mu-\nu+\lambda\mathbf{1}=\alpha} \bigl(l^T\mu - u^T\nu + \lambda\bigr)\Bigr]$$

**错误发生在**将上述 "min-max" 问题改写为单一的 "min-min" 问题：

$$\min_{\mu,\nu,\lambda,\gamma,\tau} \; l^T\mu - u^T\nu + \lambda + \tau$$

这个改写**不等价**。一般地，`min_x max_y f(x,y) ≠ min_{x,y} f(x,y)`。

#### 3.4.2 为什么不等价

原问题：先对 μ,ν,λ 求 **max**（在 α 固定的条件下），再对 α,γ,τ 求 min。

改写后：对所有变量 (μ,ν,λ,γ,τ) **同时**求 min。

由于 μ,ν,λ 在目标中带负号（`-u^T ν`），min 会驱动 ν → +∞，而 max 会阻止这种发散（因为内层 max 受 α 约束）。

#### 3.4.3 为什么会导致 unbounded

当 Σ P_upper > 1（IMDP 数据的常态），嵌套 LP 的可行域中存在使目标函数 → -∞ 的方向：

设 ν_i = M（M → ∞），μ_i = 0，λ = -2M：

1. 约束 `μ_i - ν_i + λ + γ_min ≥ 0` → γ_min ≥ 3M
2. 约束 `γ_j ≥ γ_min` → γ_j ≥ 3M
3. 约束 `δ ≥ V2[l]ᵀγ` → δ ≥ 3M（Σ V2 = 1）
4. 目标值 ≈ -uᵀν + λ + δ = -(Σ u_i)·M + (-2M) + 3M = (1 - Σ u_i)·M

当 Σ u_i = 1.9043 > 1 时，目标值 ≈ -0.9043M → **-∞**。

因此嵌套 LP **无下界**，最优值为 -∞，对任意 ε < 1 均判定 infeasible。

#### 3.4.4 与 Competitive 文档的一致性

`Competitive_Approximate_Relation_Computation.md` Section 3 断言 "LP duality cannot eliminate corner enumeration"。其分析针对的是一种不同的方法（共享原始变量的单一 LP），但结论在此处同样适用：角点枚举的几何必要性无法通过对偶技巧绕过。

嵌套对偶方法的错误属于更根本的层面——它试图将 min-max 结构平面化为单一 LP，而忽略了 min 和 max 的不对易性。

### 3.5 结论

**嵌套 LP 对偶方法（`coupling_dual.py`）在数学上不正确。** 其推导中的 `min_x max_y → min_{x,y}` 变换不等价，导致 LP 在 IMDP 的典型数据（Σ P_upper > 1）下无下界，产生大量假阴性。该方法**不可**用于 Algorithm 2。

---

## 4. 保留的代码修改

虽然 dual LP 方案被证伪，但以下代码修改已保留在代码库中：

1. **`core/approx_sim/__init__.py`** — 仍然导出 `check_coupling_dual`（供未来研究参考）
2. **`core/approx_sim/coupling_dual.py`** — 保留 `solver` 参数（不影响现有功能）
3. **`core/approx_sim/coupling.py`** — 保留 `solver` 参数（不影响现有功能）
4. **`core/approx_sim/algorithm.py`** — 保留 `method` 参数和 dual 分支（默认 `method='corner'`，向后兼容）
5. **`core/approx_sim/epsilon_search.py`** — 保留 `method` 参数透传
6. **`time_algorithm2.py`** — 保留 `--method` CLI 选项
7. **`steps/step2_epsilon_search.py`** — 保留 `--method` CLI 选项
8. **`Main_ApproxSim.py`** — 保留 `--method` CLI 选项

**注意**：`method='dual'` 路径会产生错误结果（假阴性），不应在生产中使用。它仅作为代码历史保留，供未来研究参考。

---

## 5. 后续优化方向

既然 dual LP 不可行，性能优化应聚焦于以下已验证的方向：

| 优化方向 | 原理 | 预期加速 | 投入 |
|---------|------|---------|------|
| **商业 LP 求解器** | Gurobi/Mosek 比 ECOS/SCS 快 10-50x | 10-50x | 低 |
| **Action 排序启发式** | 优先尝试匹配度高的 fine action，提前退出内层循环 | 1.5-3x | 低 |
| **Pre-filter 强化** | 添加 coarse 侧对称检查和二分图估计 | 1.1-1.5x | 低 |
| **并行策略改进** | 预计算 corner 数据，避免线程锁争用 | 1.2-2x | 低 |
| **Warm-start** | 利用上一轮迭代的对偶变量值加速求解 | 1.5-5x | 中 |
| **Lazy Corner Enumeration** | 切割平面法：按需生成角点而非全部枚举 | 2-10x | 中-高 |
| **GPU 批量 LP** | cuOpt 或 JAX 批量求解小 LP | 10-100x | 高（探索性） |

---

## 6. 相关文件

| 文件 | 说明 |
|------|------|
| `debug_dual.py` | 逐对对比 per-corner LP vs dual LP 的诊断脚本 |
| `compare_methods.py` | 完整流水线对比脚本（Test1D 案例） |
| `doc_en/performance_optimization_plan.md` | 计算瓶颈分析与其他优化方案详述 |
| `doc_en/Competitive_Approximate_Relation_Computation.md` | 竞争性语义理论与角点枚举必要性 |
| `doc_en/interval_coupling_dual.md` | 嵌套对偶 LP 的原始推导（已被证伪） |
