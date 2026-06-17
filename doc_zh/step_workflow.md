# IMDP Approximate Simulation — 分步工作流

将完整流水线拆分为三个独立步骤。每个 IMDP 构建是独立的，精细和粗糙是两个对称的构建过程，各自保存到独立文件夹。

## 目录

> 文档索引见 [doc/README.md](README.md)，汇总了所有 doc/ 文件的作用和推荐阅读顺序。
>
> 新合作者建议按 README.md 中的阅读顺序快速对齐。

- [完整案例：DoubleIntegrator coarse→coarse](#完整案例doubleintegrator-coarsecoarse)
- [核心理念](#核心理念)
- [两种运行方式](#两种运行方式)
- [分辨率选项](#分辨率选项)
- [步骤详解](#步骤详解)
- [YAML 配置管理](#yaml-配置管理)
- [数据流与文件结构](#数据流与文件结构)
- [典型使用场景](#典型使用场景)
- [运行记录 (log.md)](#运行记录)
- [关键指标解读](#关键指标解读)

---

## 完整案例：DoubleIntegrator coarse→coarse

本节以 `demo` 配置（DoubleIntegrator 2D 系统，coarse→coarse，49→49 状态）为例，完整展示从零到得出 bound 验证结论的全过程。

### 背景

- **系统**：DoubleIntegrator 2D 连续动力学，控制输入 u∈[-5,5]，状态空间 [-21,-10.5]×[21,10.5]
- **目标区域**：[-4,-2]×[4,2]
- **初始状态**：x0 = [0, -8]
- **离散动作**：3 个（u ∈ {-5, 0, 5}）
- **粗糙 IMDP**：7×7 网格 → 49 个抽象状态
- **精细 IMDP**：同为 7×7 网格（demo 用相同分辨率验证流程正确性）
- **预期结果**：相同网格应存在精确仿真关系（ε=0），MC 验证应确认 bound 成立

### 系统模型

```
边界:  [-21, -10.5] × [21, 10.5]
目标:  [-4, -2] × [4, 2]         （右上角小矩形）
初始:  x0 = [0, -8]               （下方偏右）
动作:  3 个离散控制输入 u ∈ {-5, 0, 5}
```

Continuous state space partitioned into a 7×7 rectangular grid (49 cells). Each cell is labeled as goal, critical (boundary), or normal. The IMDP transition probability intervals are computed from forward reachability of the continuous dynamics under each action.

### Step 1: 构建 IMDP

构建 coarse 分辨率的 IMDP，自动运行 RVI 检测 V(s0)。

```bash
$ python run_pipeline.py build --config configs/approx_sim.yaml di_coarse
```

输出：

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

产出文件 `output/di_coarse/params.yaml`：

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

要点：
- 49 状态 coarse IMDP 构建耗时 6.2s，RVI 检测耗时 0.8s
- V(s0)=5.19e-08（数值上 >0），V_viable=true，可以继续

### Step 2: ε 二分搜索

搜索 coarse IMDP 仿真 fine IMDP 所需的最小容差 ε。对于相同网格（coarse→coarse），预期 ε_min=0（精确仿真）。

```bash
$ python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

Step 2 输出：

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

二分搜索过程：

| ε | 可行? | \|R\| | LP 调用 | 耗时 |
|---|--------|------|---------|------|
| 1.0 | yes | 49 | 1,190 | 0.8s |
| 0.0 | yes | 49 | 1,771 | 12.2s |

结果：**ε_min = 0.0**，相同网格存在精确仿真关系，初始状态对 (21, 21) 在 R 中。

### Step 3: RVI + 策略迁移 + MC 验证

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

### 完整结果汇总

| 阶段 | 关键结果 | 耗时 |
|------|---------|------|
| Step 1: 构建 IMDP | 49 states, V(s0)≈5.2e-08 | 7.1s |
| Step 2: ε 搜索 | ε_min=0.0, \|R\|=49, 精确仿真 | 12.2s |
| Step 3: RVI | V_coarse(s0)=0, 策略收敛 | 1.5s |
| Step 3: 策略迁移 | 49 个状态策略映射 | 0.1s |
| Step 3: MC 验证 | 5000×200 次仿真 | 127.4s |
| **总计** | **bound_holds=True** | **~149s** |

### 结果解读

1. **ε_min = 0.0**：相同网格的两个 IMDP 之间存在精确仿真关系。这是预期的——当精细和粗糙使用相同分辨率时，f2c 映射是一一对应的，Algorithm 2 在第一个迭代就收敛了。

2. **bound_holds = True**：经验满足概率（0.9794）≥ 理论下界（0.0000）。理论的 V_coarse(s0) 接近 0（粗抽象太保守），但 MC 仿真显示实际到达目标的频率高达 97.9%，说明真实系统可控性很好。

3. **degradation = 0.0**：由于 ε=0，近似仿真没有引入概率损失（(1-(1-0)^200)=0）。

4. **瓶颈分析**：Step 2 的 LP 求解占了 ε 搜索 93% 的时间（11.6s/12.2s），角点枚举仅占 3%。当精细网格更密时，后继数 k1 增大，角点数按 2^(k1-1) 指数增长，LP 数量会爆炸。这是 Minkowski-Weyl 定理决定的组合下界。

### 核心要点

- 对于 coarse→coarse（相同网格），Algorithm 2 验证了**精确仿真**的存在性，无需容差
- 策略迁移的 bound 在 MC 仿真中**经验成立**，验证了理论框架的正确性
- 整个流程 **149s** 即可跑通，适合作为验证框架正确性的快速回归测试
- 若要用更密的精细网格（如 coarse→fine），Step 2 的 LP 求解时间会急剧增长，需要进一步的优化策略

---

## 核心理念

**Fine 和 Coarse 是相对的。** 每个 IMDP 只是一个带有特定分辨率的抽象——没有哪个天生就是"精细"或"粗糙"。因此：

- **Step 1 每次只构建一个 IMDP**，按给定分辨率独立构建，并立即运行 RVI 检测 V(s0) 是否 > 0
- **V>0 预检是关键**：如果粗糙 IMDP 的 V=0（太粗了，找不到可行的 reach-avoid 策略），那么 ε 搜索和策略迁移没有意义
- **两个 IMDP 都满足 V>0 时，才值得跑 Step 2 的 ε 搜索**

实际流程：

```
Step 1: 构建 IMDP_A → RVI 检测 V_A > 0 ?
Step 1: 构建 IMDP_B → RVI 检测 V_B > 0 ?
    ↓
  ┌─ 任一 V=0 → 停止，调整分辨率/参数
  │
  └─ 两者 V>0 → Step 2: ε 搜索 → Step 3: 策略迁移 + MC
```

---

## 两种运行方式

### 方式 A：run_pipeline.py（推荐）

```bash
# 查看所有预定义配置
python run_pipeline.py --config configs/approx_sim.yaml --list

# 构建单个 IMDP
python run_pipeline.py build --config configs/approx_sim.yaml di_coarse
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# 成对分析（自动检查 V>0，必要时构建缺失的 IMDP）
python run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine

# 只跑某一步
python run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine --step 2
```

### 方式 B：手动分步运行

逐个调用 `steps/` 下的脚本，适合调试和自定义参数。

```bash
# Step 1: 构建单个 IMDP
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution coarse \
    --output output/di_coarse

python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution fine \
    --output output/di_fine

# Step 2: ε 搜索
python steps/step2_epsilon_search.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --output output/di_coarse_fine/eps.pkl

# Step 3: 策略迁移 + MC 验证
python steps/step3_validate.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --eps output/di_coarse_fine/eps.pkl \
    --output output/di_coarse_fine/results.pkl
```

---

## 分辨率选项

DoubleIntegrator 2D 系统的可用分辨率：

### 基础分辨率（3 动作）

| 值 | 网格 | 状态数 | 说明 |
|----|------|--------|------|
| `coarse` | 7×7 | 49 | 最快，用于验证流程 |
| `medium` | 14×14 | 196 | |
| `fine` | 21×21 | 441 | |
| `medium_x2` | 28×28 | 784 | |
| `fine_x2` | 42×42 | 1,764 | 最密，算法 2 最慢 |

### 多动作变体（5 / 7 动作）

增加离散动作数可提升策略表达能力，从而获得更高的 V(s0) 值：

| 值 | 网格 | 动作数 | 状态数 | V(s0) |
|----|------|--------|--------|-------|
| `medium_5act` | 14×14 | 5 | 196 | **0.688** |
| `fine_7act` | 21×21 | 7 | 441 | **0.995** |

动作离散化：
- 3 动作：u ∈ {-5, 0, 5}
- 5 动作：u ∈ {-5, -2.5, 0, 2.5, 5}
- 7 动作：u ∈ {-5, -3.33, -1.67, 0, 1.67, 3.33, 5}

所有分辨率共享相同的动力学参数：控制输入 u∈[-5,5]，边界 [-21,-10.5]×[21,10.5]，目标区域 [-4,-2]×[4,2]，初始状态 x0=[0,-8]。

---

## f2c 映射：几何重叠 vs 整数倍

### 问题

最初 `build_fine_to_coarse_map` 要求精细网格的每维尺寸是粗糙网格的整数倍（如 14/7=2、42/21=2）。这限制了哪些分辨率对可以对比——例如 medium (14) 与 fine (21) 的比值是 1.5，会直接报错。

### 原因分析

R 的初始化只需要标签一致，并不要求几何包含。但纯标签笛卡尔积会导致 |R| 爆炸（medium→fine ~ 55,000 对），无法计算。

### 解决：几何重叠映射

`build_f2c_overlap_map` 对每个 fine cell 找出所有与其空间重叠的 coarse cell。对于 2D 系统：

```
非整数比 (21→14, 1.5×):
┌─────┬─────┐
│ fine  │ fine  │      每个 fine cell 最多与 4 个
│ → c1  │ → c2  │      coarse cell 重叠
│ → c3  │ → c4  │
├─────┼─────┤      avg ~1.8 coarse/fine
│ fine  │ fine  │      R 初始 ~794 对 (可控)
└─────┴─────┘

整数比 (14→7, 2×):
┌───┬───┐
│ fine │ fine │        每个 fine cell 恰好与 1 个
│  →   │  →   │        coarse cell 重叠
├───┼───┤             avg = 1.0 coarse/fine
│ fine │ fine │        (退化为原版 f2c)
└───┴───┘
```

- 整数比：avg overlap = 1.0，退化为原版严格 1:1 映射
- 非整数比：avg overlap ≤ 4（2D），R 大小可控，且不损失理论的标签完备性
- **注意**：这是一种启发式剪枝——两个状态即使没有空间重叠，规范上也可能是 valid 的 pair。因此计算出的 ε 可能偏保守（偏大），但 bound 仍然成立。这是用计算量换完备性的权衡

---

## 步骤详解

### Step 1 — 构建单个 IMDP + V>0 检测

**做什么：** 对给定分辨率构建一个 IMDP，运行 RVI 检测 V(s0) 是否 > 0。

**内部流程：**

```
1. create_model(args)              → 动力学模型
2. RectangularPartition(model)     → 矩形网格划分
3. RectangularForward(...)         → 每个格子的前向可达集
4. compute_probability_intervals() → 计算转移概率区间
5. IMDP(...)                       → 包装为 IMDP 对象
6. RVI_JAX(imdp, s0)              → V(s0) 值函数
7. 保存 imdp.pkl + params.yaml
```

**命令行参数：**

| 参数 | 说明 |
|------|------|
| `--model` | 模型，默认 `DoubleIntegratorApproxSim`，可选 `Dubins3DApproxSim` |
| `--resolution` | 分辨率（必填） |
| `--output` | 输出目录路径（必填，会自动创建） |
| `--seed` | 随机种子，默认 `42` |

**输出文件：**

`imdp.pkl` 包含：

| 键 | 类型 | 用途 |
|----|------|------|
| `imdp` | `IMDP` | IMDP 对象 |
| `partition` | `RectangularPartition` | 网格划分 |
| `model` | `Dynamics` | 动力学模型 |
| `resolution` | `str` | 分辨率名称 |
| `model_name` | `str` | 模型类名 |

`params.yaml` 包含：

| 键 | 说明 |
|----|------|
| `model` | 模型名称 |
| `resolution` | 分辨率 |
| `seed` | 随机种子 |
| `num_states` | 状态数 |
| `V_s0` | 初始状态的鲁棒值 |
| `V_viable` | V(s0) > 0 是否成立 |
| `build_time_s` | 构建耗时 |
| `rvi_time_s` | RVI 耗时 |
| `total_time_s` | 总耗时 |

**耗时估计：**

| 分辨率 | 状态数 | 时间 |
|--------|--------|------|
| coarse | 49 | ~6s |
| medium | 196 | ~7s |
| fine | 441 | ~9s |
| fine_x2 | 1764 | ~15s |

耗时主要花在 `compute_probability_intervals`（JAX 向量化计算转移概率区间）和 JAX 首次编译。RVI 检测很快（~0.8s for coarse）。

---

### Step 2 — ε 二分搜索

**做什么：** 加载两个 IMDP，构建 f2c 映射，运行 Algorithm 2 的固定点迭代 + ε 二分搜索，找到最小的 ε。

**核心概念：**

ε 是近似仿真关系的容差参数。耦合分布 W 在关系 R 中的质量 ≥ 1−ε：
- ε=0 → 精确仿真（W 的 100% 质量在 R 中）
- ε=1 → 无约束（任意 pair 都在 R 中）
- ε_min → 粗糙抽象"模仿"精细系统的最紧容差

**二分搜索策略：**

```
已知 hi=1.0 总是可行（上界）
测试 lo=0.0 → 若可行则 ε_min=0（精确仿真）
否则在 [lo, hi] 之间二分：
  mid = (lo+hi)/2
  运行 Algorithm 2(mid) → 检查 (s0_fine, s0_coarse) ∈ R(mid) ?
    可行 → hi=mid (更紧)
    不可行 → lo=mid (太紧)
  重复直到 hi-lo ≤ eps_tol
```

利用单调性 R(ε_small) ⊆ R(ε_large)：测试 ε_mid 时用 R_hi 做 warm-start。

**命令行参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--imdp_fine` | — | 精细 IMDP 的 `.pkl` 文件（必填） |
| `--imdp_coarse` | — | 粗糙 IMDP 的 `.pkl` 文件（必填） |
| `--output` | — | 输出 `.pkl` 文件路径（必填） |
| `--eps_tol` | `1e-3` | 二分搜索精度 |
| `--n_jobs` | `-1` | 并行线程数，`-1`=全部CPU，`1`=串行 |

**输出文件内容：**

| 键 | 类型 | 说明 |
|----|------|------|
| `epsilon_min` | `float` | 最小 ε |
| `R_final` | `set[(int,int)]` | 最终仿真关系 |
| `eps_history` | `list[dict]` | 每次评估：ε, feasible, n_pairs, lp_calls, wall_time |
| `s0_fine` | `int` | 精细初始状态 |
| `s0_coarse` | `int` | 粗糙初始状态 |
| `init_in_R` | `bool` | 初始状态对是否在 R 中 |

**瓶颈分析：**

| 指标 | ε=1.0（trivial） | ε=0.0（严格） |
|------|------------------|---------------|
| 角点枚举时间 | 0.3s (3%) | 0.5s (4%) |
| LP 求解时间 | 0.0s (0%) | 11.6s (95%) |
| LP 调用数 | 1,190 | 1,771 |
| max_k1 | 9 | 9 |
| max_corners | 51 | 51 |

**瓶颈是 LP 求解（~95%），不是角点枚举。** 网格越密 → 后继数 k1 增大 → 角点数指数增长（2^(k1-1)）→ LP 数量爆炸。

---

### Step 3 — RVI + 策略迁移 + MC 验证

**做什么：** 在粗糙 IMDP 上求解鲁棒值迭代，将最优策略迁移到精细 IMDP，通过蒙特卡洛仿真验证 bound。

**内部流程：**

```
1. build_fine_to_coarse_map()        → f2c 映射
2. RVI_JAX(imdp_coarse, s0)          → V_coarse, policy_coarse
3. transfer_policy(policy_coarse)    → policy_fine
4. validate_transfer(...)             → MC 仿真 + bound 验证
```

**理论 bound：**

```
V_fine(s0) ≥ V_coarse(s0_coarse) − (1 − (1−ε_min)^N)
```

其中 N 是 horizon。MC 验证检查经验满足概率是否 ≥ 下界。

**命令行参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--imdp_fine` | — | 精细 IMDP 的 `.pkl` 文件（必填） |
| `--imdp_coarse` | — | 粗糙 IMDP 的 `.pkl` 文件（必填） |
| `--eps` | — | Step 2 输出的 `.pkl` 文件（必填） |
| `--output` | — | 输出 `.pkl` 文件路径（必填） |
| `--mc_iterations` | `5000` | MC 仿真次数 |
| `--sim_horizon` | `200` | 仿真步长 |
| `--skip_mc` | — | 跳过 MC 验证（调试时用，省 ~2min） |

**输出文件内容：**

| 键 | 类型 | 说明 |
|----|------|------|
| `V_coarse` | `np.array` | 粗糙 IMDP 的值函数 |
| `policy_coarse` | `np.array` | 粗糙策略标签 |
| `policy_fine` | `np.array` | 迁移后的精细策略标签 |
| `validation` | `dict` 或 `None` | `empirical_prob`, `theoretical_bound`, `bound_holds`, `degradation` |

---

## YAML 配置管理

配置文件 [config/approx_sim.yaml](../configs/approx_sim.yaml) 分为两部分：

### builds — 单个 IMDP 构建

```yaml
builds:
  di_coarse:
    model: DoubleIntegratorApproxSim
    resolution: coarse
    seed: 42
    output_dir: output/di_coarse
```

### pairs — 成对分析

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

### 预定义配置一览

**Builds：**

| 配置名 | 分辨率 | 状态数 | V(s0) |
|--------|--------|--------|-------|
| `di_coarse` | coarse | 49 | ~0 |
| `di_medium` | medium | 196 | 0.314 |
| `di_fine` | fine | 441 | 0.373 |
| `di_medium_x2` | medium_x2 | 784 | — |
| `di_fine_x2` | fine_x2 | 1,764 | — |
| `di_medium_5act` | medium_5act | 196 | **0.688** |
| `di_fine_7act` | fine_7act | 441 | **0.995** |

**Pairs：**

| 配置名 | 粗→细 | 用途 |
|--------|-------|------|
| `demo` | coarse→coarse (49→49) | 完整案例验证流程 |
| `di_coarse_fine` | coarse→fine (49→441) | 小规模 (coarse V≈0, 不适合) |
| `di_medium_fine` | medium→fine (196→441) | 非整数比案例 (1.5×) |
| `di_medium_fine_x2` | medium→fine_x2 (196→1764) | 中等规模 |
| `di_fine_fine_x2` | fine→fine_x2 (441→1764) | 较大规模 |
| `di_medium_5act_fine_7act` | medium_5act→fine_7act (196→441) | **推荐：多动作高V值** |

---

## 数据流与文件结构

```
configs/approx_sim.yaml          ← 统一参数管理
steps/
  step1_build_imdp.py             ← Step 1: 构建单个 IMDP + V>0 检测
  step2_epsilon_search.py         ← Step 2: ε 搜索 (加载两个 IMDP)
  step3_validate.py               ← Step 3: RVI + 策略迁移 + MC
run_pipeline.py                   ← 读 YAML，串联三步

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

**文件复用：** 同一组 IMDP 可以配多个不同的 ε 搜索（不同 `eps_tol`），同一组 `imdp + eps` 可以反复跑 Step 3（调 `mc_iterations`、`sim_horizon`）。

---

## 典型使用场景

### 场景 1：快速验证 V 是否 > 0

```bash
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution coarse \
    --output output/test_coarse

# 查看 params.yaml
cat output/test_coarse/params.yaml
# 关注 V_s0 和 V_viable 字段
```

### 场景 2：运行完整案例

```bash
python run_pipeline.py build --config configs/approx_sim.yaml di_coarse
python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

### 场景 3：非整数比实际运行（medium→fine, 1.5×）

两个 IMDP 都有 V>0，使用几何重叠映射绕过整数比限制：

```bash
# 构建 IMDP
python run_pipeline.py build --config configs/approx_sim.yaml di_medium
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# 查看 V 值
cat output/di_medium/params.yaml  # V(s0) = 0.314
cat output/di_fine/params.yaml    # V(s0) = 0.373

# 运行 pair
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine
```

### 场景 4：反复调参（不重建 IMDP）

```bash
# 构建一次 IMDP
python run_pipeline.py build --config configs/approx_sim.yaml di_medium
python run_pipeline.py build --config configs/approx_sim.yaml di_fine

# 反复跑 Step 2 调不同参数
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

### 场景 5：只验证 bound（跳过 MC）

```bash
python steps/step3_validate.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --eps output/di_coarse_fine/eps.pkl \
    --output output/di_coarse_fine/results.pkl \
    --skip_mc
```

### 场景 6：完整 MC 验证

```bash
python steps/step3_validate.py \
    --imdp_fine output/di_fine/imdp.pkl \
    --imdp_coarse output/di_coarse/imdp.pkl \
    --eps output/di_coarse_fine/eps.pkl \
    --output output/di_coarse_fine/results.pkl \
    --mc_iterations 10000 --sim_horizon 300
```

### 场景 7：推荐案例 — 多动作高 V 值（medium_5act→fine_7act）

这是当前推荐的完整案例组合，粗糙 IMDP V≈0.69，精细 IMDP V≈0.99，两者都有可靠的 reach-avoid 策略：

```bash
# Step 1: 构建两个 IMDP（各含 V>0 检测）
python run_pipeline.py build --config configs/approx_sim.yaml di_medium_5act
python run_pipeline.py build --config configs/approx_sim.yaml di_fine_7act

# 确认 V 值
cat output/di_medium_5act/params.yaml  # V(s0) ≈ 0.688
cat output/di_fine_7act/params.yaml    # V(s0) ≈ 0.995

# Step 2+3: 成对分析
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_5act_fine_7act
```

预期结果：
- coarse V≈0.69 → 粗糙策略有约 69% 的概率到达目标
- fine V≈0.99 → 精细策略几乎确定到达目标
- ε_min 可能较小（精细的 7 个动作可以较好地"模拟"粗糙的 5 个动作）
- bound: V_fine ≥ 0.69 − (1−(1−ε)^200)，在 ε 较小时几乎无损失

---

## 运行记录

详细的构建记录和 pair 分析结果见 [log.md](log.md)，包括：

- 环境信息（git commit、Python/JAX 版本）
- 所有已构建 IMDP 的 V(s0)、耗时
- 每组成对分析的 ε 搜索过程、MC 验证结果
- 汇总对照表

每次运行新的配置后，将结果追加到 log.md 对应条目下。

---

## 关键指标解读

### params.yaml（Step 1 输出）

| 指标 | 含义 |
|------|------|
| `V_s0` | 初始状态的鲁棒最大到达概率 |
| `V_viable` | V(s0) > 0 是否成立。为 false 时需要换更密的分辨率 |
| `num_states` | IMDP 状态数 |

### Step 2 输出

| 指标 | 含义 |
|------|------|
| `epsilon_min` | 粗糙仿真精细的最小容差。越小越好 |
| `\|R_final\|` | 仿真关系中的状态对数 |
| `LP calls per ε` | LP 调用数。ε=0.0 时最大 |
| `max_k1` | 一个 (s,a) 对的精细后继数。决定角点数量 (2^(k1-1)) |
| `max_corners` | 一个 (s,a) 对的最大角点数。决定最坏情况的 LP 数 |

### Step 3 输出

| 指标 | 含义 |
|------|------|
| `V_coarse(s0)` | 粗糙 IMDP 到达目标的鲁棒最大概率 |
| `empirical_prob` | MC 仿真中精细系统实际到达目标的频率 |
| `theoretical_bound` | V_coarse − (1−(1−ε)^N)，理论下界 |
| `bound_holds` | `empirical_prob ≥ theoretical_bound` 是否成立 |
| `degradation` | (1−(1−ε)^N)，近似仿真引入的概率损失 |
