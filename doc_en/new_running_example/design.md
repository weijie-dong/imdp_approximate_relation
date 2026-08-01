# 新 Running Example 设计 + sound 分层 `check_coupling` 实现方案

> 本文档记录：为配合 sound 分层耦合检查方法 (`method='tiered'`) 的构建与验证，
> 重新设计 running example 使其**对 competitive 与 cooperative 两种语义都不平凡**，
> 并给出分层方法的实现与三级验证流（running → 1D → 2D）。
>
> 关联文档（`doc_en/lazy_enum_review/`）：`formal_lower_bound_theorem.md`（已证括号
> `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB`）、`lazy_enum_soundness_analysis.md`（shipped lazy
> 不 sound）、`STATUS_AND_ROADMAP.md` §2.6（ε 是输出）。

---

## 0. 背景与动机

- shipped 的 `method='lazy'` 耦合检查**不 sound**：对偶给出 `g` 的*上*界，只能证不可行、
  不能证可行。sound 下界理论已证明（括号 + `LB*≥1−ε⟹可行`、`UB<1−ε⟹不可行`）。
- 经"ε 是输出"重新定位后，唯一可用的 sound 方法是 **(a) 分层设计**：保留 Theorem V.3
  角枚举作为 sound 保底（Tier 3），只捷径易部分（不可行侧 LP-free `UB`，大 ε 可行迭代 `LB*`）。
  紧 ε 可行核仍枚举（§3 屏障，不可约）。Tier 2（lazy 违例搜索）**去掉**（`UB` 已覆盖其唯一
  有用的不可行侧，其可行侧正是 unsound 的）。
- running example 原参数对 competitive 平凡（ε_min=0），需微调使其对两种语义都不平凡。
- 本次只实现 **competitive（Algorithm 2）**；cooperative（Algorithm 1）暂不做，但新 running
  example 已选成对两种语义都不平凡，将来补 cooperative 时同一例可直接用。

---

## 1. 新 running example 参数（对两种语义都不平凡）

### 1.1 问题诊断

原例 competitive 平凡（ε_min=0），因为 p1 总能选动作 α——α 的两个角 (0.1,0.9)、(0.6,0.4)
对 γ、δ 都精确可配，p1 永远避开 β 的硬角 (0,1)。competitive (∀a2∃a1) 下 p1 自选 a1，
硬角不咬人。原例的 (0,1) 硬角是 **cooperative（∀a1∃a2）** 现象：p1 被迫处理自己所有动作。

### 1.2 微调

把 `P2(p2,δ)` 的 q2 下界 0.1→0.2（等价 r2 上界 0.9→0.8），其余不动。手算复核：

- **competitive (Algorithm 2) ε_min = 0.1**
  - a2=δ：α 的角 (0.1,0.9) 需 μ2(r2)≥0.9，但 δ 现 r2≤0.8 → 最佳配对 W(R)=0.9
    （μ2=(0.2,0.8)：W(q1,q2)=0.1, W(r1,r2)=0.8）。β 的 (0,1)→0.8。best a1=α→0.9 ⟹ ε≥0.1。
  - a2=γ：仍 1.0（α 精确防御）。
  - ⇒ comp ε_min = max(1−1.0, 1−0.9) = 0.1。**硬角 = α 的 (0.1,0.9)**。

- **cooperative (Algorithm 1) ε_min = 0.1**
  - a1=β：角 (0,1) 对任何 a2 都 ≤0.9（γ 的 r2≤0.9），best a2=γ→0.9；角 (0.6,0.4)→1.0。
  - a1=α：用 γ 精确防御→1.0。
  - ⇒ coop ε_min = max(1−1.0, 1−0.9) = 0.1。**硬角 = β 的 (0,1)**（原例硬角保留）。

⇒ **同一微调例**：comp ε_min=0.1（α 硬角）、coop ε_min=0.1（β 硬角），两种语义都不平凡，
且各自有不同的硬角。自环对 (q1,q2)/(r1,r2) 两种语义都 g=1，故 ε_min 全由 (p1,p2) 决定。

### 1.3 固定参数（t 不再是自由变量，ε 由搜索输出）

M2 的 γ 取 t=0（q2∈[0.1,0.6]，与 P1(p1,α) 重合，"易匹配"对）；δ 微调（q2∈[0.2,0.8]）。

**M1**（状态 0=p1, 1=q1, 2=r1；动作集 p1→{α,β}，q1→{α自环}，r1→{β自环}）：

| state | action | successors | P_lower | P_upper |
|---|---|---|---|---|
| p1 | α | [q1, r1] | [0.1, 0.0] | [0.6, 1.0] |
| p1 | β | [q1, r1] | [0.0, 0.0] | [0.6, 1.0] |
| q1 | α | [q1] | [1.0] | [1.0] |
| r1 | β | [r1] | [1.0] | [1.0] |

**M2**（状态 0=p2, 1=q2, 2=r2；动作集 p2→{γ,δ}，q2→{γ自环}，r2→{δ自环}）：

| state | action | successors | P_lower | P_upper |
|---|---|---|---|---|
| p2 | γ | [q2, r2] | [0.1, 0.0] | [0.6, 1.0] |
| p2 | δ | [q2, r2] | [0.2, 0.0] | [0.8, 1.0]   ← 微调：下界 0.1→0.2 |
| q2 | γ | [q2] | [1.0] | [1.0] |
| r2 | δ | [r2] | [1.0] | [1.0] |

标签：p1/p2=normal，q1/q2=goal，r1/r2=critical。f2c 一对一（p1→p2, q1→q2, r1→r2）。
初始状态 s_init = p1/p2 = 0。

### 1.4 角点（枚举确认）

- P1(p1,α): (0.1,0.9), (0.6,0.4)
- P1(p1,β): (0.0,1.0), (0.6,0.4)
- P2(p2,γ): (0.1,0.9), (0.6,0.4)
- P2(p2,δ): (0.2,0.8), (0.8,0.2)   ← 微调后

---

## 2. 分层方法设计：`check_coupling_tiered`

新模块 `core/approx_sim/coupling_tiered.py`，单函数，签名与 `_check_pair` 已有数据对齐：

```python
def check_coupling_tiered(pl1, pu1, succ1, pl2, pu2, succ2, corners2,
                           R_local, epsilon, tol=1e-8, solver=None):
    """sound + complete 的逐 (s1,a1,s2,a2) 耦合可行性检查。

    Tier 1 (LP-free):  UB, LB_min  via coupling_bounds.compute_bounds_lpfree
                       UB  < 1-eps  -> 不可行 (sound)
                       LB_min >= 1-eps -> 可行 (sound, 弱; 免费赢)
    Tier 1.5 (1 LP):   LB*  via coupling_bounds.compute_lb_star
                       LB* >= 1-eps -> 可行 (sound)   [k1>22 跳过]
    Tier 3 (精确):     corners1 = enumerate_corners(pl1,pu1);
                       for c1 in corners1: check_coupling(c1, corners2, ...)
                       任一不可行 -> 不可行; 否则可行  (exact)

    返回 dict: feasible, decided_by('ub_infeas'/'lbmin_feas'/'lbstar_feas'/
              'enum_infeas'/'enum_feas'/'skipped'), lp_calls, lp_time,
              n_corners_enum, n_corners_total。
    """
```

要点：
- **复用已 sound 模块**——`coupling_bounds.compute_bounds_lpfree`（LP-free UB/LB_min）、
  `compute_lb_star`（1-LP LB\*）、`coupling.check_coupling` + `corners.enumerate_corners`（Tier 3）。
  无新数学，定理已证。
- **Tier 3 与 `corner` 基线逐字节相同**（同 `enumerate_corners` → 同 `check_coupling` 循环），
  故残差上 `tiered == corner` *by construction*；只看 Tier 1/1.5 多快截掉。
- **保留 lazy 角枚举**：`corners1` 仅在落到 Tier 3 时才枚举（bounds 跨越 `1−ε`）。
  不可行侧 0 枚举——即 50.8h 案里 ~40h 那块的速度来源。
- `k1 > MAX_K1_BRUTE (22)`：bounds 返回 None/跳过 → 直落 Tier 3。sound（无捷径），仅无加速。
  2D 是否触发由 Tier C 实测暴露。

---

## 3. 集成进 `compute_approx_sim`

`core/approx_sim/algorithm.py`：
1. import：`from .coupling_tiered import check_coupling_tiered`。
2. a2 循环（~180 行）捕获当前丢弃的 coarse bounds：
   `corners2, succ2, pl2, pu2 = _get_corners(2, s2, a2_pos)`（原为 `_, _`）。
3. 在 `_check_pair` 中 `method=='dual'`/`'lazy'` 旁（236–253 行）加臂：
   ```python
   elif method == 'tiered':
       succ1, pl1, pu1 = _get_bounds(1, s1, a1_pos)   # 便宜，不枚举角
       result = check_coupling_tiered(
           pl1, pu1, succ1, pl2, pu2, succ2, corners2,
           R_frozen, epsilon, solver=lp_solver)
       lp_calls += result['lp_calls']; lp_time += result['lp_time']
       all_ok = result['feasible']
   ```
   `_get_bounds`（不枚举角）前置获取；`corners1` 在 `check_coupling_tiered` 内部仅 Tier-3 残差时枚举。
4. `method='tiered'` 经 `compute_min_epsilon(..., method='tiered')` 透传——`epsilon_search.py`
   已原样转发 `method`。

---

## 4. soundness 修复：`corners.py` halfspace fallback（roadmap Step 6）

`core/approx_sim/corners.py` 的 `_enumerate_halfspace_reduced` 在 `HalfspaceIntersection`
抛异常时回退到 `_enumerate_lp`，后者**不 sound**（只取坐标极值顶点 → 漏顶点 → 可能保留本该
删除的对）。这会同时削弱 `corner` 基线与 Tier 3。

修复：`HalfspaceIntersection` 抛异常时 **raise `SoundnessError`**（或返回哨兵让调用方按
"无法 sound 枚举"处理），不再静默调 `_enumerate_lp`；更新 docstring。若 2D 上有 `(s,a)` 的
`k1>12` 且多胞体退化，这会作为真实 soundness 发现暴露——那是该报告的，不是该掩盖的。
（Test1D `k1≤9` 全走 greedy，无影响。）

---

## 5. running example 构造（走核心 Algorithm 2）

新脚本 `doc_en/new_running_example/run_running_example_pipeline.py`：
- 用轻量 stand-in 类构造 M1/M2 为真实可计算的 IMDP 对象（**绕过** `IMDP.__init__` 的
  `partition.x2state` 等重组装路径），直接设 `P_full`、`S_id`、`actions_inputs`、`s_init`。
  - `P_full` 用 list-of-ndarrays（按 state）以支持异构动作数（p1 两动作、q1/r1 各一）；
    `S_id[s][a]` 为后继 ID 数组。存**原始**区间界（如 δ: P_low=[0.2,0.0], P_up=[0.8,1.0]）。
  - partition stub：仅需 `.size`、`.goal['bools']`、`.critical['bools']`（compute_approx_sim/
    compute_min_epsilon 只用这些 + `imdp.s_init`）。
  - `f2c_map = [[0],[1],[2]]`；`action_order=False`（避免访问 `actions_inputs` 的全局索引）。
- 调 `compute_min_epsilon(method='tiered')` 与 `method='corner'`，断言 ε_min 与 |R| 一致
  （预期 ε_min≈0.1，|R|=3 at ε_min，|R|=2 略低于）。
- 另在论文固定 ε ∈ {0, 0.1, 0.2, 0.5} 上跑 `compute_approx_sim`，对照手推 retain/remove。
- 同步更新 `doc_en/running_example/validate_lower_bound_running_example.py` /
  `k1_3_subexample.py`：(i) δ 改微调值；(ii) 改为 import `coupling_bounds` 真实模块
  （不再手抄 L1/U2/L2/Phi/M_c）；(iii) 额外调 `check_coupling_tiered` 逐对，展示 tier 决策
  == 精确 g 决策 + 命中哪层。
- 更新 `doc_en/running_example/example_description.md` 的手推数值（§3–§5 retain/remove 表
  随微调重算）。

---

## 6. 三级验证流

### Tier A — running example（走核心算法，competitive）
`run_running_example_pipeline.py`：tiered vs corner，ε_min/|R| 一致 + 固定 ε 的 retain/remove
对照手推 + 逐对 `decided_by`。预期 comp ε_min≈0.1（非平凡），硬角 α 的 (0.1,0.9)。

### Tier B — 1D（整条管线，competitive）
- `compare_methods.py`（Test1D 15→5）：method 列表加 `'tiered'`；断言
  `tiered.epsilon_min == corner.epsilon_min` 且 `|R|` 一致（`tol` 内）；报 LP 调用下降 +
  wall-time 加速 + 逐对 `decided_by` 直方图。
- `scalable_test.py` 在 21→7、35→7、51→17：跨规模与 ε 表征残差枚举比例（多少 sub-pair 落 Tier 3）。

### Tier C — 2D（整条管线，case-study 规模，competitive）
- `time_algorithm2.py --method corner` vs `--method tiered`，DoubleIntegrator **49→441**
  （文档里的 `di_coarse_fine`）先跑；比 ε_min、|R|、时间、残差比例。若 49→441 可行且时间允许，
  再试 **196→441**（`di_medium_fine`，50.8h 那案）直接测不可行侧加速。

---

## 7. 关键文件

- **新建**：`core/approx_sim/coupling_tiered.py`（分层检查）；
  `doc_en/new_running_example/run_running_example_pipeline.py`（running 走算法）。
- **改**：`core/approx_sim/algorithm.py`（import + `method='tiered'` 臂 + 捕获 `pl2,pu2`，
  ~180 / ~236–253 行）。
- **改**：`core/approx_sim/corners.py`（halfspace fallback 改 raise，Step 6）。
- **改**：`doc_en/running_example/validate_lower_bound_running_example.py`、
  `k1_3_subexample.py`、`example_description.md`（δ 微调值 + 复用真实模块 + 调 tiered）。
- **改**：`compare_methods.py`、`scalable_test.py`、`time_algorithm2.py`（method 列表加 `'tiered'`）。
- **复用不改**：`core/approx_sim/coupling_bounds.py`、`coupling.py`(`check_coupling`)、
  `epsilon_search.py`(`compute_min_epsilon`)。

---

## 8. 验证方法

1. **单元（Tier A）**：running example 逐对 `tier-决策 == g-决策`、括号 `LB_min ≤ LB* ≤ g ≤ UB`
   成立；固定 ε 的 retain/remove 与手推一致。
2. **精确性（Tier B）**：`compare_methods.py` 报 `tiered == corner`（ε_min、|R|）PASS on 15→5；
   `scalable_test.py` 同口径在 21→7/35→7/51→17 成立。
3. **soundness 性质**：15→5 上，tiered 判可行的每对都 `g ≥ 1−ε`（`compute_exact_g` 真值），
   判不可行都 `g < 1−ε`；无 false-feasible。
4. **规模（Tier C）**：49→441 `tiered == corner`（ε_min/|R|）；报加速 + 残差比例；暴露任何
   `k1>22` 跳过或 halfspace `SoundnessError` 作为发现。
5. **运行环境**：`C:/Users/DWJ/.conda/envs/dyabstract/python.exe`（cvxpy/numpy）；
   `core.jax_config`（非 `jaxconfig`）。

---

## 9. 范围外（明确）

- 不做 Tier 2 / lazy 违例搜索（已决策去掉）。
- ~~不做 cooperative（Algorithm 1）实现——本次只 competitive~~ **【2026-08-01 更新：已完成】**
  cooperative（Algorithm 1 FCE + Algorithm 3 BCV）已实现并 toy 验证通过，见
  `doc_zh/cooperative_implementation_plan.md` 与验证脚本
  `doc_en/new_running_example/run_cooperative_validation.py`。本微调例 coop ε_min≈0.1 已复现。
  引擎入口：`compute_approx_sim(..., semantics='cooperative')` / CLI `--semantics cooperative`。
- 无新理论（已证）；不动 `lazy_enum.py` 的 shipped unsound 路径（仅留作未用，单独文档注记）。
- Dubins3D（3D）不在本轮；2D DoubleIntegrator 为 case-study 目标。

---

## 10. 三方互证结果（已跑通）

脚本 `run_running_example_pipeline.py`（dyabstract env）跑通，**tiered == corner == 手算**
三方一致：

**[1] 逐对精确 g（(p1,p2) 的 4 个 (a1,a2) 子对）— code == hand：**

| a1 | a2 | g_code | g_hand | ok |
|---|---|---|---|---|
| α | γ | 1.0000 | 1.0 | Y |
| α | δ | 0.9000 | 0.9 | Y |
| β | γ | 0.9000 | 0.9 | Y |
| β | δ | 0.8000 | 0.8 | Y |

**[2] competitive ε_min（compute_min_epsilon, tol=1e-4）：**
tiered=0.1000, corner=0.1000, hand=0.1，|R|=3 → **AGREE**。

**[3] 固定 ε 下 (p1,p2) 的 retain/remove — tiered==corner==hand（全 Y）：**

| ε | thr | tiered | corner | hand | ok |
|---|---|---|---|---|---|
| 0.000 | 1.000 | False | False | False | Y |
| 0.050 | 0.950 | False | False | False | Y |
| 0.099 | 0.901 | False | False | False | Y |
| 0.101 | 0.899 | True | True | True | Y |
| 0.200 | 0.800 | True | True | True | Y |
| 0.500 | 0.500 | True | True | True | Y |

边界干净：0.099→删 (p1,p2)，0.101→留。

**[4] tiered 逐对决策 @ ε=0.1（边界）— 关键发现：**

| a1 | a2 | feas | decided_by | enum/total | g_hand |
|---|---|---|---|---|---|
| α | γ | True | enum_feas | 2/2 | 1.00 |
| α | δ | True | enum_feas | 2/2 | 0.90 |
| β | γ | True | enum_feas | 2/2 | 0.90 |
| β | δ | **False** | **ub_infeas** | **0/0** | 0.80 |

- **(β,δ)**（真不可行，g=0.8<0.9）由 **LP-free UB 直接 sound 判不可行，0 角枚举**——
  正是分层方法在不可行侧的免费加速，toy 上已显出来。
- 其余三个可行对落到 `enum_feas`（枚举全部 2 个角）——符合理论：紧 ε 可行侧 LB\* 有 gap、
  证不了可行，回落 Tier 3 枚举（§3 屏障）。
- competitive (p1,p2) @ ε=0.1 → **RETAINED**（α 防 δ），与手算一致。

**结论**：代码（tiered 与 corner）与手算在 toy 上逐位一致；tiered==corner（精确性）成立；
且 tiered 的 LP-free UB 在不可行侧实现了 0 枚举加速——sound 且有效。下一步按 plan 进 Tier B（1D Test1D）。

---

## 11. Tier B 结果（1D Test1D）— 已跑通，无 bug

### 11.1 全 ε 搜索精确性（`compare_methods.py`，corner vs tiered，15→5，tol=1e-3）

| Metric | corner | tiered |
|---|---|---|
| epsilon_min | 0.000977 | 0.000977 |
| \|R_final\| | 15 | 15 |
| total LP calls | 7755 | 4570 |
| wall time (s) | 93.0 | 68.0 |

- epsilon_min **MATCH**；|R_final| **MATCH**；逐迭代轨迹 **MATCH**（12 vs 12 iters，0 mismatch）。
- **[PASS] tiered == corner**：精确匹配。LP 1.70x 下降、wall 1.37x 加速。
- ε=0.0 那次 tiered 用 **0 LP**（LP-free UB 全员判不可行）即得 |R|=0——不可行侧免费加速的缩影。

### 11.2 逐 sub-pair soundness（`check_tiered_soundness.py`，tiered 决策 vs 精确 g）

对 135 个 sub-pair，逐对比较 tiered.feasible 与 ground-truth `g ≥ 1−ε`（边界 ±1e-6 跳过）：

| ε | feas | infeas | boundary | tier 直方图 | false-feasible | false-infeasible |
|---|---|---|---|---|---|---|
| 0.05 | 85 | 50 | 0 | ub_infeas:50, lbstar_feas:55, enum_feas:30 | 0 | 0 |
| 0.10 | 85 | 50 | 0 | ub_infeas:50, lbstar_feas:55, enum_feas:30 | 0 | 0 |
| 0.50 | 105 | 30 | 0 | ub_infeas:30, lbstar_feas:105 | 0 | 0 |

- **0 false-feasible（sound）+ 0 false-infeasible（complete）**，跨 ε=0.05/0.1/0.5 全 PASS。
- tier 分布随 ε 漂移符合理论：
  - ε=0.5（易体制）：**0 enum**，100% 由 bounds 判（与 step2 "ε=0.5 零残差"一致）。
  - ε=0.05/0.1（紧体制）：105/135=78% 免枚举（50 UB + 55 LB\*），仅 30 个（全可行）落 Tier 3——
    紧 ε 可行核残差，§3 屏障。

**结论**：Tier B 无 bug。tiered 在 Test1D 上**逐 sub-pair sound+complete**，与 corner 基线
精确一致，且加速来自不可行侧（UB，0 枚举）与易可行侧（LB\*），紧 ε 可行核仍枚举——
完全符合理论预期。下一步进 Tier C（2D DoubleIntegrator）。

---

## 12. Tier C（2D DoubleIntegrator 49→441）— 发现性能瓶颈（非 bug）

### 12.1 k1 分布（缓存 IMDP 探测）

| | n(s,a) | k1 min | k1 max | max 角数 | 平均角数 | 总顶点 | k>12 | k>22 |
|---|---|---|---|---|---|---|---|---|
| coarse(49) | 105 | 4 | 9 | 51 | 16.9 | 1,771 | 0 | 0 |
| fine(441) | 1029 | 9 | **12** | **1408** | 386.9 | **398,118** | 0 | 0 |

- **无 halfspace、无 bounds-skip**（k1 全 ≤12 ≤22）：Step 6 的 halfspace soundness 问题在此 case
  **不触发**；tiered bounds 全程生效；corner 走 greedy（sound）。
- 但 fine 侧角点极多（每 (s,a) 最多 1408、均值 387、合计 39.8 万顶点）——2D corner 枚举瓶颈。

### 12.2 发现：LB\* LP 在 k1=12 上是瓶颈（tiered 紧 ε 反而慢）

实测 tiered ε=0.0 iter 0：**~7 秒/对**（4 对/16s），441 对 ~50min 仅一个 iter。
根因：k1=12 时 `compute_lb_star` 的 LP 有 **2^12 = 4096 条约束**，每个 sub-pair 都建+解一次
（cvxpy 建 4096 约束 + HIGHS 解 ~200ms）；而 ε=0（thr=1）时 LB\* 几乎不可能证可行（g<1），
这 4096-约束 LP **全是白开销**。corner 在 ε=0 反而短路快（找到第一个不可行角即停，~1 LP）。

- **这是性能问题，不是正确性 bug**：tiered 仍 sound+complete，只是紧 ε 在大 k1 上比 corner 慢。
- 与理论一致（§2.6）：有用体制（小 ε、系统接近）正是 sound 验证最贵、bounds 帮不上忙的地方；
  2D 的 ε_min 小 → 成本主要由紧 ε 可行核（387 角枚举）主导，两种方法都贵，bounds 只救易部分。

### 12.3 候选修复（待定，未实现）

1. **LB\* 前插入"最难角探针"**（sound，1 LP）：先 check 最可能违反的角；若不可行 → 直接判不可行
   （1 LP，省掉 4096-约束 LB\*）。这是 sound 的单角见证，**不是**被撤回的 unsound lazy
   （无割平面循环、无"收敛⇒可行"）。能救 loose-UB 不可行侧，但非最难角违反时会 miss。
2. **sound lazy 违例搜索**（即旧 lazy 的 False-path，本就 sound）：割平面找违反角，比单角探针可靠，
   但等于把撤回的 Tier 2 的 sound 半边加回来——需你确认。
3. **LB\* 约束剪枝**：2^k1 约束中大量被支配，可剪枝降 LP 规模（保留 sound 需谨慎）。
4. **接受现状**：2D 上 tiered ≈ corner（紧 ε 可行核主导），bounds 只在易部分有效——如实写进论文。

### 12.4 现状

- tiered 在 2D 仍 sound+complete，但紧 ε 因 LB\* 大 LP 变慢；corner 也未跑完（估 ~15-30min）。
- **未拿到 2D 的 ε_min/|R| 对比**（两方法都没跑完整 ε 搜索）。
- 待你决定 12.3 的修复方向后再重跑 2D 取数。

### 12.5 探针（选项 1）已实现 + 实测

实现了"最难角探针"（`_hardest_corner` + Tier 1.25，sound：可行 c1-集凸、P1=conv(角)，
故任一点不可行 ⟹ 某角不可行 ⟹ 对不可行）。Test1D soundness 复跑 **PASS 无回归**
（探针在 Test1D 不触发——UB 够紧；0 false-feasible/infeasible）。

2D ε=0.0 实测：**50min → 20min**（7756 LP，588 pre-filtered）。探针**部分生效**：
只救"最难角恰好是违反角"的对；其余 loose-UB 不可行对仍落 LB\*（4096-约束 LP 白跑）→ enum
找真违反角。

### 12.6 更深层发现：LB\* 在大 k1 紧 ε 是负债

- ε=0（不可行侧）：corner 短路 ~1 LP/对（第一个违反角即停）很快；tiered 因 LB\* 4096-约束 LP
  反而慢（20min）。**corner 在此处比 tiered 快。**
- ε≥ε_min（可行侧，易体制）：LB\* 证可行 → 省 387-角枚举，比 corner 快。
- ε≈ε_min（紧可行核）：LB\* 有 gap → 枚举 + LB\* 开销，略慢于 corner。

根因：k1=12 时 LB\* LP 有 2^12=4096 约束（~150ms/次），比 corner 短路（1-5 个小 LP ~25ms）贵。
**LB\* 只在 k1 小时（Test1D k1≤5，32 约束）划算。** 这与 §2.6 一致：有用体制（紧 ε）正是
bounds 帮不上的地方。

### 12.7 候选：k1-自适应开关（未实现，待定）

按 k1 自适应：**k1 > K_LB\*（如 8）时跳过 LB\* 和探针**，只用 UB 预过滤 + corner 枚举
（sound：跳过 LB\* 只是多枚举，仍精确，tiered==corner 仍成立）。小 k1 保留 LB\*（Test1D 那种快）。
这样 2D 上 tiered ≥ corner（UB 救不可行侧、无 LB\* 开销），Test1D 上仍享 LB\* 加速。

2D 完整 ε 搜索估 ~2-3h（紧 ε 可行核 387-角枚举主导，两方法都贵）。加 12.7 的开关后不可行侧
iter 可近 corner 速度，但紧 ε 可行 iter 仍慢（§3 屏障）。

### 12.8 k1-自适应开关已实现（K_LBSTAR=8）+ 2D 实测

实现了 `K_LBSTAR = 8`：k1≤8 用 LB\*+探针（Test1D k1≤5、35→7 k1=7-8 享加速）；k1≥9 跳过 LB\*+探针，
只 UB + corner 枚举。Test1D soundness 复跑 **PASS 无回归**。

2D ε=0.0 实测（K=8）：仍 ~15min（926s LP，7644 LP）。LP 数几乎没降（7756→7644）——说明 ε=0 瓶颈
**不是 LB\***（已跳过），而是 check_coupling LP 本身：2D 规模每个 LP ~120ms（W 矩阵 ~100+ 变量），
7644 个 = 926s。且 **UB（Tier1，k1=12 → 2^12=4096 子集纯 Python）在 ε=0 几乎没证出不可行**（441 对
全落 enum），~9min Python 开销是纯浪费 —— 2D 上 UB 也是负债。

ε=0.5（可行 iter）：~6s/对（8 核并行）→ 44min/iter，全枚举 387 角（可行无短路）× ~5 可行 iter
→ **2D 整体 ~2.5h**。这是 §3 屏障（紧 ε 可行核，sound 方法不可约）——corner 也一样贵。

### 12.9 结论：2D 是 §3 屏障的实证

- 2D（k1=9-12、387 角、紧 ε 可行核）上 **tiered ≈ corner**：bounds（UB/LB\*）在大 k1 紧 ε 都不划算
  （UB 松、LB\* 大 LP 负债），可行核 387-角枚举两方法都跑。唯一差异是 UB 的 ~9min/iter Python 开销
  （ε=0 上是纯浪费）——可再 gate 掉 UB（k1>K_FULL 时纯 corner-enum），但 2D 仍 ~2.5h（可行核主导）。
- 这**正是 §2.6 的论断**：有用体制（紧 ε、系统接近）是 sound 验证最贵、bounds 帮不上的地方；
  2D case study 是该论断的实证。bounds 的加速只在**小 k1 / 易体制**（Test1D、35→7）显现。
- 论文叙事：Test1D（小 k1）展示 tiered 的 sound 加速；2D（大 k1 紧 ε）展示 §3 屏障——bounds 不能
  消除最坏情形，诚实定位。

### 12.10 现状（已定：大规模交集群）

- **2D run 已杀掉**：笔记本跑不动 2D（~2.5h/方法，§3 屏障），且本机交互期间 CPU 被抢导致 8h+ 膨胀。
- **小模型验证完整**（代表性）：running example 三方互证（§10）、Test1D 15→5 全 ε+逐 sub-pair
  （§11）、Test1D 21→7 全 ε——均 **PASS，无 bug**。35→7 / 51→17 等余下规模交集群同事跑
  （见 `cluster_handoff.md` §4.1）。
- **大规模交集群**：2D 49→441 / 196→441 的执行命令、预期、判 PASS 判据、已知行为，全部写在
  **`cluster_handoff.md`**。同事在集群上跑 corner vs tiered，回传 ε_min/|R|/时间/LP 数，填论文
  case study 表。
- **代码就绪**：`method='tiered'` 已集成（`coupling_tiered.py` + `algorithm.py` 臂 +
  `time_algorithm2.py`/`compare_methods.py` 选项），小模型验证 sound+complete。无已知 bug。
  待修（不影响本批案例）：`corners.py` k1>12 halfspace unsound fallback（roadmap Step 6）。





