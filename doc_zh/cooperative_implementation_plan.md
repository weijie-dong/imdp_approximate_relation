# Cooperative 语义实现计划（Algorithm 1 FCE / Algorithm 3 BCV）

> 对应论文 `iMDP-apb.tex`：§V-B（Algorithm 1 cooperative FCE）、§VI（Algorithm 3 cooperative BCV）。
> 现有引擎 `core/approx_sim/` 只实现了 competitive（Algorithm 2 / 4）。本计划补全 cooperative。

## 实现状态：✅ 核心完成 + toy 验证全过（2026-08-01）

Step 1–6 全部落码并通过 toy（论文 Example 1 / `new_running_example`）三方互证：

| Step | 内容 | 状态 |
|---|---|---|
| 1 | cooperative 耦合原语（V2_union 收集 + 公共后继空间嵌入） | ✅ `algorithm.py:_get_coarse_union` |
| 2 | cooperative FCE 驱动（Algorithm 1，`semantics='cooperative'` 分支） | ✅ `algorithm.py:_check_pair` |
| 3 | cooperative BCV 界（顶点枚举 Lemma polytope-ext + LB*coop） | ✅ `coupling_bounds.py` 新增 4 函数 |
| 4 | cooperative BCV 驱动（Algorithm 3） | ✅ `coupling_tiered.py:check_coupling_tiered_coop` |
| 5 | 接线（argparse `--semantics` + 补 `tiered` choices + config/run_pipeline） | ✅ Main_ApproxSim/step2/run_pipeline |
| 6 | toy 验证 | ✅ 见下 |

**toy 验证结果**（`run_cooperative_validation.py`，对照 `design.md` §1.2 手算）：
- [1] cooperative ε_min = **0.1000** = hand ✓（硬角 = β 的 (0,1)）
- [2] 固定 ε retain/remove of (p1,p2)：6 个 ε 全 match ✓
- [3] coop vs comp @ ε=0.1：都留 (p1,p2)，|R|=3 ✓
- [4] **BCV == FCE**（完备性 Cor. `cor:completeness`）：ε_min 0.1=0.1，retain/remove 全 match ✓
- [5] 逐 sub-pair soundness：tiered 决策 vs `compute_exact_g_coop` 真值，跨 ε={0.05,0.1,0.5}，
  **0 false-feasible / 0 false-infeasible**；tier 分布与 competitive toy 镜像
 （β @ ε=0.05 由 LP-free **ub_infeas** 判不可行 0 枚举；ε=0.5 由 **lbstar_feas**；紧可行由 enum_feas）✓

**修过的一个 bug**：`_get_coarse_union` 初版在持 `_cache_lock` 时调 `_get_corners`（后者也锁同一把
非重入 `threading.Lock`）→ cooperative 首次调用即死锁；competitive 不走 union 缓存故未暴露。
修复：union 计算不持锁，`_get_corners` 自身线程安全，仅最终写 `_union_cache` 时加锁。

**未做（沿用 competitive 的 cluster-handoff 模式）**：Test1D 15→5 / 2D 49→441 规模的 cooperative
ε_min/计时。代码就绪，可在集群上跑 `--semantics cooperative --method {corner,tiered}` 取数填论文。
competitive 已在 design.md §10–12 跑过同口径三方互证。

---

## 0. 关键校正：cooperative ≠ "∀a1 ∃a2 找一个粗动作防御"

## 0. 关键校正：cooperative ≠ "∀a1 ∃a2 找一个粗动作防御"

勘察初稿曾把 cooperative 当作 competitive 的内外循环对换（∀a1 ∃a2，找一个 coarse 动作当 defender）。**这与论文矛盾，必须按论文实现。**

论文（Def `def:Coupling Constraint for Corners` line 1317、Thm `thm:IMDP-coupling-constraint` item(i)、§VI line 1790）明确：cooperative 的粗侧响应是**对所有 coarse 动作的随机化混合** ρ∈Dis(Γ2(x2))，化简为单一凸组合，顶点集

```
V2 = ⋃_{a2∈Γ2(x2)} C(x2,a2)        # 全动作角点并集
Q  = conv(⋃_{a2} P2(x2,a2))         # 响应多面体
```

所以 cooperative 驱动里**没有 a2 循环**：

```
competitive (已实现, algorithm.py:179-288):
    for a2 in Γ2(x2):              # ∀a2
        for a1 in Γ1(x1):         #   ∃a1 (找 defender)
            for c1 in C(x1,a1): check_coupling(c1, V2=C(x2,a2))   # ∀c1
            if all feasible: found; break
        if not found: remove (x1,x2)

cooperative (待实现, Algorithm 1):
    for a1 in Γ1(x1):              # ∀a1
        V2_union = ⋃_{a2} C(x2,a2)
        for c1 in C(x1,a1):        #   ∀c1
            if not check_coupling(c1, V2=V2_union) feasible: remove (x1,x2); break
```

**好消息**：`coupling.py:check_coupling(c1, V2, succ1_ids, succ2_ids, R_local, epsilon)` 的构造本就是
"细侧固定角点 c1（∀），粗侧用 β 混合 V2（∃）"——这正是 cooperative 的角色分工
（细侧=被模拟者 M1 是 ∀ 对手，粗侧=M2 是 ∃ 响应者）。所以 **cooperative FCE 直接复用 `check_coupling`**，
只是 V2 取"全动作角点并集"。competitive 也复用它，只是 V2 取单动作角点。**不需要镜像公式。**

> ⚠️ 现有 toy 脚本 `doc_en/running_example/validate_lower_bound_running_example.py:217-227`
> 把 cooperative 当成"纯 a2 选择"（`max over a2 of g(a1,a2)`）暴力算。这**不是**论文的随机化响应——
> 纯动作选择是欠近似，关系会比 union 形式小（论文 line 778：随机化 "strictly necessary"、能扩大关系）。
> 引擎版实现后要和这个 toy 对账/替换。

## 1. 算法差异速查表

| 维度 | Competitive（已实现） | Cooperative（待实现） |
|---|---|---|
| 响应多面体 Q | `P2(x2,a2)` 单动作 box–simplex | `conv(⋃_{a2} P2(x2,a2))` 全动作并集 |
| 顶点集 V_Q | `C(x2,a2)` 单动作角点 | `⋃_{a2} C(x2,a2)` 并集（超集，sound） |
| FCE 驱动内层 | for a2, for a1, for c1（找 found） | for a1, for c1（任一不可行即删；无 a2 循环） |
| 耦合 LP 的 V2 | `C(x2,a2)` | `⋃_{a2} C(x2,a2)` |
| BCV 极端质量 U2/L2 | box–simplex 闭式（Lemma `lem:boxsimplex`） | 多面体顶点枚举（Lemma `lem:polytope-ext`） |
| BCV-Check 其余 Tier | 相同（语义无关） | 相同 |
| g_Q 定义 | `min_{c∈C(P1)} max_{q∈Q} Φ(c,q)` | 同（Q 不同而已） |

## 2. 核心实现挑战：粗侧跨动作的公共后继空间

cooperative 的 V2 是**跨所有 a2 的角点并集**。不同 a2 的后继集 `succ2(a2)` 可能不同。
`check_coupling` 要求 V2 每个角点是同长 k2 的向量、且 succ2_ids 长度 = k2。
因此必须把每个动作的角点**嵌入到公共后继空间**：

```
succ2_union = dedup(⋃_{a2∈Γ2(x2)} succ2(a2))      # 公共粗后继 ID 集
对每个 a2, 每个 c2 ∈ C(x2,a2):
    v_embed = zeros(|succ2_union|)
    对 succ2(a2) 的第 t 个后继 sid:
        v_embed[ index(sid in succ2_union) ] = c2[t]
    V2_union.append(v_embed)
```

这样 V2_mat 是 [L × |succ2_union|]，W 是 [k1 × |succ2_union|]，与 `check_coupling` 接口完全兼容。
R_local 的 (s1,s2) 对照用真实 state ID，不受嵌入影响。

## 3. 分步实施（落到文件/函数）

### Step 1 — Cooperative 耦合原语（小）  `corners.py` / `coupling.py`
- 新增 `build_coarse_union(imdp2, s2, _get_corners)`：
  收集 `succ2_union`（ID 列表，去重保序）+ `V2_union`（嵌入后的角点列表）。
- 复用现有 `enumerate_corners` / `_get_corners`（每个 (x2,a2) 角点已缓存）。

### Step 2 — Cooperative FCE 驱动（Algorithm 1）  `algorithm.py`
- `_check_pair`（line 162）加 cooperative 分支：
  ```
  for a1 in range(num_a1):
      corners1, succ1, pl1, pu1 = _get_corners(1, s1, a1)
      # 细侧预过滤（沿用现有 fine_has_r，但 succ2_set 改为 succ2_union_set）
      for c1 in corners1:
          if not check_coupling(c1, V2_union, succ1, succ2_union, R_frozen, epsilon, ...):
              return ((s1,s2), ...)        # 任一不可行即删
  ```
- 无 a2 循环、无 found_defender。
- `compute_approx_sim`（line 30）加 `semantics='competitive'` 参数，分发到对应分支。
- 预过滤 `succ2_set` 要用 union（因粗响应可落在任意 a2 的后继上）。

### Step 2 验证 — 对账 toy
- 用新引擎算 `new_running_example` 的 cooperative ε_min，与 `design.md` 记录值对照。
- 确认 ≥ 纯 a2 暴力版（随机化应扩大关系，即 ε_min 应 ≤ 纯 a2 版）。
- 若不符，先查嵌入/后继空间是否正确。

### Step 3 — Cooperative BCV 界  `coupling_bounds.py`
现有 `compute_bounds_lpfree(pl1,pu1,succ1,pl2,pu2,succ2,R)` 把粗侧当 box–simplex（区间闭式算 U2/L2）。
cooperative 的 Q=conv(⋃ P2(x2,a2)) **不是** box–simplex，需用**多面体顶点枚举**（Lemma `lem:polytope-ext`）：
`min_{q∈Q} q(S) = min_{v∈V_Q} v(S)`，`max = max_{v∈V_Q} v(S)`，V_Q = ⋃ C(x2,a2)（超集，sound）。

改动：
- 新增 `compute_bounds_lpfree_coop(pl1,pu1,succ1, V_Q, succ2_union, R)`：
  子集枚举 A⊆U 不变（细侧），但 U2/L2 改为"枚举 V_Q 顶点取极值"。
- 新增 `compute_lb_star_coop(...)`：q* ∈ conv(V_Q) 约束
  （`q* = β @ V_Q_mat, β≥0, Σβ=1`），而非区间 box 约束。
- 重构建议：把"粗侧取极值"抽成策略（box 闭式 vs 顶点枚举），两语义共用 UB/LB_min/LB* 主干。

### Step 4 — Cooperative BCV 驱动（Algorithm 3）  `coupling_tiered.py`
- 加 cooperative 分支：Tier1（LP-free coop 界）→ Tier1.25（最难角点探针 LP，V2=union）→
  Tier1.5（LB* coop）→ Tier3（逐角点 `check_coupling(c1, V2_union)`，== FCE）。
- 挂成 `method='coop_tiered'`（或 `semantics='cooperative'` + `method='tiered'`）。

### Step 5 — 接线
贯穿 `semantics`（或 `coop` 标志）+ `method` 到：
- `epsilon_search.compute_min_epsilon`
- `steps/step2_epsilon_search.py`（line 49 的 `--method` choices）
- `Main_ApproxSim.py`（line 108-110 argparse choices）
- `run_pipeline.py` / `configs/approx_sim.yaml`

**顺手修老问题**：`Main_ApproxSim` 与 `step2` 的 argparse `choices` 都漏了 `tiered`，一并补上。

### Step 6 — 验证
1. **完备性**（Corollary `cor:completeness`）：同一基准上 cooperative FCE == cooperative BCV
   （关系 R 与 ε_min 字节级一致）。
2. **计时**：小基准上 cooperative FCE vs BCV，验证加速。
3. **与 competitive 对照**：cooperative 无 a2 循环 + 随机化扩大关系，应更快且 ε_min ≤ competitive 的对应值。

## 4. 决策记录
- 代码组织：**现有文件加分支**（algorithm.py / coupling_bounds.py / coupling_tiered.py 内加 cooperative 分支，靠 `semantics` 参数分发）。复用最大化、与 competitive 并列好对照。
- 落地节奏：**先 FCE 后 BCV**。Step1+2 先跑通 cooperative FCE 并对账 toy，确认语义正确后再做 Step3+4 BCV。分阶段验证、风险低。

## 5. 关键文件指针
- `core/approx_sim/algorithm.py:30` `compute_approx_sim`（dispatcher）；`:162` `_check_pair`（competitive ∀a2∃a1 在 :179-288）
- `core/approx_sim/coupling.py:16` `check_coupling`（复用）；`:197` `check_coupling_max_mass`
- `core/approx_sim/corners.py:44` `enumerate_corners`；`:24` `get_successor_info`
- `core/approx_sim/coupling_bounds.py:87` `compute_bounds_lpfree`；`:172` `compute_lb_star`；`:142` `compute_exact_g`
- `core/approx_sim/coupling_tiered.py:115` `check_coupling_tiered`
- `core/approx_sim/epsilon_search.py` `compute_min_epsilon`
- `steps/step2_epsilon_search.py:49` argparse choices；`Main_ApproxSim.py:108-110` argparse choices
- toy 参考：`doc_en/running_example/validate_lower_bound_running_example.py:217-227`（纯 a2 暴力，欠近似）；`doc_en/new_running_example/design.md:33-48`（语义说明与 ε_min 记录）
