# 大规模案例执行手册（交集群同事）

> 📗 英文版：`cluster_handoff_EN.md`（同一内容，给英文同事）。

> 本文档供有计算集群的同事执行大规模 IMDP approximate-simulation 案例使用。
> 目标：在集群上跑 **`method='tiered'`**（sound 分层耦合检查）与 **`method='corner'`**
> （sound 精确基线）并对照，确认两者 ε_min / |R| 一致（精确性），并取加速比/残差比例
> 用于论文 case study。
>
> 配套设计文档：`doc_en/new_running_example/design.md`（方法设计 + 小模型验证结果 +
> 2D 性能发现）。本手册只讲**怎么跑、看什么**。

---

## 0. 一句话结论

- `method='tiered'` 是 sound + complete 的分层耦合检查：LP-free UB/LB_min（不可行/弱可行证）
  + 最难角探针 + LB\*（紧可行下界） + 角枚举保底（== corner 基线）。
- **k1 ≤ 8** 用全部分层（bounds 划算）；**k1 ≥ 9** 跳过 LB\*+探针（大 k1 上 LB\* LP 是负债），
  只 UB + 角枚举。跳过 LB\* 只是多枚举，仍精确，`tiered == corner` 仍成立。
- 小模型已在本机验证 **无 bug**（见 §3）。大规模请在集群上跑 §4 的命令。

---

## 1. 环境准备

```bash
# 必须用 dyabstract conda 环境（cvxpy/numpy/jax 已配好）
PYTHON="C:/Users/DWJ/.conda/envs/dyabstract/python.exe"   # Windows
# 集群 Linux 上等价：激活含 cvxpy+jax+scipy 的 conda env
cd imdp-synthesis   # 仓库根

# 冒烟测试（应打印三方互证 PASS）
$PYTHON doc_en/new_running_example/run_running_example_pipeline.py
```

依赖：`cvxpy`（LP，默认 `HIGHS`）、`jax`+`jaxlib`、`scipy`（HalfspaceIntersection）、`numpy`、`tqdm`。

---

## 2. 代码状态（已就绪，已测）

新增/修改文件：
- **新增** `core/approx_sim/coupling_tiered.py` — `check_coupling_tiered()`（分层检查，含
  `K_LBSTAR=8` 自适应开关 + `_hardest_corner` 探针）。
- **改** `core/approx_sim/algorithm.py` — import + `method=='tiered'` 臂（~180 行捕获 `pl2,pu2`，
  ~236–253 行加臂）；`_get_corners(2,...)` 现返回 `(verts, succ, pl, pu)`。
- **改** `time_algorithm2.py` — `--method` 选项加 `'tiered'`。
- **改** `compare_methods.py` — 方法列表改为 `['corner','tiered']`，加逐迭代 PASS/FAIL；
  支持命令行参数 `n_fine n_coarse`。
- **新增** `check_tiered_soundness.py` — 逐 sub-pair tiered vs 精确 g 的 soundness 检查。
- **新增** `doc_en/new_running_example/run_running_example_pipeline.py` — running example 三方互证。

未改（复用）：`core/approx_sim/coupling_bounds.py`（已证 sound bounds）、`coupling.py`
（`check_coupling`）、`epsilon_search.py`（`compute_min_epsilon` 透传 `method`）、`corners.py`。

---

## 3. 已验证的小模型（本机，无 bug）

| 案例 | 检查 | 结果 |
|---|---|---|
| running example（微调 δ，3 态） | tiered == corner == 手算（逐对 g、ε_min=0.1、固定 ε retain/remove） | **PASS**（design.md §10） |
| Test1D 15→5（k1≤5） | 全 ε 搜索 tiered==corner（ε_min=0.000977, \|R\|=15, 12 iter 0 mismatch） | **PASS**（LP 1.70x↓, wall 1.37x↓） |
| Test1D 15→5 | 逐 sub-pair tiered vs 精确 g（ε=0.05/0.1/0.5） | **PASS**（0 false-feasible, 0 false-infeasible） |
| Test1D 21→7（k1=5） | 全 ε 搜索 tiered==corner（ε_min=0.000977, \|R\|=21, 0 mismatch） | **PASS**（LP 1.43x↓） |

> 结论：`method='tiered'` 在小模型上 **逐 sub-pair sound + complete**，与 corner 基线**精确一致**。
> 同一代码路径用于大规模，无新 bug 风险。

---

## 4. 大规模案例执行命令（集群）

> **重要**：corner 与 tiered 必须**分开先后跑**，不要并发（都 `n_jobs=-1` 占满 CPU，并发会互相
> 饿慢——本机已踩坑）。IMDP 构建结果会缓存到 `.cache_imdps/`，第二次起秒载。

### 4.0 实验计划一览

下列实验由小到大。**目的** = 为什么跑；**预期** = 正确（sound+complete）结果长什么样。按顺序跑；
任一**预期**不达标即停并反馈（那是 bug）。

| # | 实验 | 目的 | 命令（corner 与 tiered 各跑） | 预期结果 | ~耗时 |
|---|---|---|---|---|---|
| 0 | 冒烟测试 | 确认代码在小例上 sound+正确 | `python doc_en/new_running_example/run_running_example_pipeline.py` | 三方 PASS：`tiered==corner==手算`，ε_min=0.1，\|R\|=3(ε≥0.1)/2(ε<0.1) | 秒级 |
| 1 | Test1D 35→7 | 精确性 tiered==corner，k1=7-8（保留 LB\*+探针） | `compare_methods.py 35 7` | `[PASS]`；ε_min & \|R\| 一致；0 mismatch | 分钟 |
| 2 | Test1D 51→17 | 精确性 tiered==corner，k1=9（跳过 LB\*+探针） | `compare_methods.py 51 17` | `[PASS]`；ε_min & \|R\| 一致；0 mismatch | 分钟 |
| 3 | Test1D 逐 sub-pair soundness | 证 0 false-feasible & 0 false-infeasible（K_LBSTAR=8 边界） | `check_tiered_soundness.py 35 7 0.1` 与 `... 51 17 0.1` | `0 false-feasible + 0 false-infeasible` | 各 1-2 min |
| 4 | 2D 49→441（case-study 主案） | 取 case-study ε_min + tiered vs corner 加速比；实证 §3 屏障 | `time_algorithm2.py --coarse_resolution coarse --fine_resolution fine --method {corner,tiered}` | ε_min & \|R\| **一致**；~2.5h/方法；tiered 救不可行侧 ε-iter（UB 免枚举） | ~2.5h/方法 |
| 5 | 2D 196→441（50.8h 那案） | 实证大规模不可行侧加速 | `time_algorithm2.py --coarse_resolution medium --fine_resolution fine --method {corner,tiered}` | ε_min & \|R\| 一致；tiered 不可行 ε-iter 大幅加速（原 ~40h） | 超长 |

**每个实验的交付物**：案例 + method + `epsilon_min` / `|R_final|` / `total wall time` /
`total LP calls` + `[PASS/FAIL]` 行（见 §8）。这些数值填入论文 case study 表。

详细命令与逐项说明见 §4.1–§4.4（= 实验 1–5）。

### 4.1 Test1D 中等规模（补全小→大过渡，~分钟级）

**目的**：跨 k1 阈值确认 `tiered == corner` 精确性——k1=7-8（35→7）保留 LB\*+探针，k1=9（51→17）
跳过。两条路径都必须与 corner 一致。

```bash
# 35→7（k1=7-8，覆盖 K_LBSTAR=8 保留 LB* 边界）
$PYTHON compare_methods.py 35 7
# 51→17（k1=9，覆盖跳过 LB*+探针边界）
$PYTHON compare_methods.py 51 17
# 逐 sub-pair soundness（实验 3，更严；35→7 约 1-2 min）
$PYTHON check_tiered_soundness.py 35 7 0.1
$PYTHON check_tiered_soundness.py 51 17 0.1
```

**预期**：末尾 `[PASS] tiered == corner: exact match` + `per-iteration trajectory: MATCH`。
ε_min 与 |R| 两方法逐位一致（数值本身随规模变，无固定预期值，只验一致）。逐 sub-pair：
`0 false-feasible + 0 false-infeasible`。

### 4.2 2D DoubleIntegrator 49→441（case-study 主案例，~2.5h/方法）

**目的**：论文主 case-study 结果——ε_min/|R|、tiered 对 corner 的加速比，以及 §3 屏障的实证
（紧 ε 可行核对 sound 方法不可约）。

```bash
# 先 corner（基线，建 IMDP 并缓存）
$PYTHON time_algorithm2.py --coarse_resolution coarse --fine_resolution fine --method corner --eps_tol 1e-3
# 再 tiered（复用缓存）
$PYTHON time_algorithm2.py --coarse_resolution coarse --fine_resolution fine --method tiered --eps_tol 1e-3
```

**预期**（两份 `TIMING SUMMARY`）：
- `Epsilon minimum` 与 `|R_final|` **必须一致**（这是 sound+complete 的精确性证据）。
- `total wall time` / `Phase 3` 时间 + `Epsilon evaluations` 表（每 ε 的 LP calls / wall）。
- 记录 tiered 对 corner 的 LP 调用下降比与 wall 加速比。

**预期行为**（design.md §12 实测）：
- fine k1=9-12，角点 39.8 万、每 (s,a) 最多 1408 —— 紧 ε 可行核 387-角枚举主导，两方法都 ~2.5h
  （§3 屏障，sound 方法不可约）。
- tiered 在不可行侧 ε-iter 由 UB 免枚举（快）；可行侧紧 ε 核仍枚举（与 corner 同）。
- ε=0.0 那次：corner 短路快；tiered 因 UB 在大 k1 松（~4096 子集纯 Python 开销）可能略慢于 corner
  ——这是已知行为（bounds 在大 k1 紧 ε 帮不上，§2.6），不是 bug。

### 4.3 2D DoubleIntegrator 196→441（论文 50.8h 那案，超长）

**目的**：实证 `tiered` 的 UB 预过滤在大规模上显著加速不可行侧 ε-iter（原 50.8h corner 的 ~40h），
而 ε_min 可行 iter 仍枚举（§3 屏障）。

```bash
$PYTHON time_algorithm2.py --coarse_resolution medium --fine_resolution fine --method corner --eps_tol 1e-3
$PYTHON time_algorithm2.py --coarse_resolution medium --fine_resolution fine --method tiered --eps_tol 1e-3
```

**预期**：同 4.2——ε_min/|R| 一致；tiered 不可行 ε-iter 大幅加速（UB 免枚举）；ε_min 可行 iter 仍
枚举。**仅在有充足机时/集群时跑**。

### 4.4 其他可选（YAML 管线，替代入口）

```bash
$PYTHON run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine      # 49→441
$PYTHON run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine      # 196→441
```
（`run_pipeline.py` 默认 `model='DoubleIntegratorApproxSim'`；可在 yaml 里把 `method` 设 `tiered`。
同 4.2/4.3 的 case，替代 CLI。）

---

## 5. 如何判 PASS（精确性判据）

每个案例，corner 与 tiered 两份输出对比：
1. `epsilon_min`：`abs(corner - tiered) <= eps_tol`（一般应**完全相等**，因 Tier 3==corner）。
2. `|R_final|`：相等。
3. `compare_methods.py` 会自动打印 `[PASS] tiered == corner` + 逐迭代 `0 mismatches`。
4. （可选严检）`check_tiered_soundness.py`：逐 sub-pair `0 false-feasible + 0 false-infeasible`。

任一不匹配 = bug，请把该案例的 `epsilon_min`/`|R|`/mismatch 行反馈。

---

## 6. 已知行为 / 注意事项（不是 bug）

- **K_LBSTAR=8**（`coupling_tiered.py`）：k1≥9 跳过 LB\*+探针。若想让中 k1 也用 LB\*，调高此值
  （但 k1≥10 时 LB\* LP 有 2^k1 约束，紧 ε 反而变慢，见 design.md §12.6）。
- **UB 在大 k1 紧 ε 是开销**：k1=12 时 Tier1 枚举 2^12=4096 子集（纯 Python ~50ms/sub-pair），
  紧 ε 下 UB 常松、不证出不可行，是开销。若 2D 上想纯 corner 速度，可在 `check_coupling_tiered`
  里把 Tier1 也 gate 到 `k1 <= K_LBSTAR`（即大 k1 纯 corner-enum）；sound 不变。
- **halfspace soundness**：本批案例 k1 全 ≤12（走 greedy，sound），不触发 `corners.py` 的
  halfspace/LP-fallback。若大规模出现 k1>12，halfspace 路径在 `HalfspaceIntersection` 抛异常时会
  **不 sound 地**回退 `_enumerate_lp`（roadmap Step 6 未修）——届时请反馈，需改成 raise。
- **`method='lazy'` 仍 unsound**，勿用于正式结果（仅 `corner`/`tiered` 是 sound 的）。
- **CPU 竞争**：corner/tiered 都 `n_jobs=-1`，务必串行跑，勿并发。

---

## 7. 反馈格式

跑完每个案例，请回传：
- 案例 + 方法 + `epsilon_min` / `|R_final|` / `total wall time` / `total LP calls`。
- `compare_methods.py` 的 `[PASS/FAIL]` 行（或手算对比）。
- 异常/mismatch 的完整行。

这些数值填入论文 case study 表（design.md §11/§12 已有小模型 + 2D 性能发现框架）。
