# Algorithm 2 Timing Benchmark

对 IMDP 竞争近似仿真（Algorithm 2）进行端到端时间测量，使用 DoubleIntegrator 2D 系统。

## 快速开始

```bash
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution coarse --fine_resolution fine
```

## 分辨率配置

| 参数值 | number_per_dim | 状态数 | 动作数 |
|--------|---------------|--------|--------|
| `coarse` | [7, 7] | 49 | 3 |
| `medium` | [14, 14] | 196 | 3 |
| `fine` | [21, 21] | 441 | 3 |
| `medium_x2` | [28, 28] | 784 | 3 |
| `fine_x2` | [42, 42] | 1,764 | 3 |

## 测量流程

### Step 1 — 快速验证正确性（最小网格）

```bash
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution coarse --fine_resolution fine
```

确认输出：
- `ε_min` 在 [0, 1] 范围内
- `init_in_R: True`
- 无报错

### Step 2 — 逐步放大网格，记录时间

```bash
# (196 → 1,764)
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution medium --fine_resolution fine_x2

# (441 → 1,764)
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution fine --fine_resolution fine_x2
```

第二次起 IMDP 自动从 `.cache_imdps/` 加载，只计 Phase 3 时间。

### Step 3 — 同网格调参复测

```bash
# 调整搜索精度
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution fine --fine_resolution fine_x2 --eps_tol 1e-4

# 调整并行线程数
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution fine --fine_resolution fine_x2 --n_jobs 8

# 串行运行（用于对比加速比）
conda run -n dyabstract python -u time_algorithm2.py \
    --coarse_resolution fine --fine_resolution fine_x2 --n_jobs 1
```

### Step 4 — 分析

每次运行末尾输出摘要，关注以下指标：

| 指标 | 含义 |
|------|------|
| `Phase 3 (Epsilon search)` | Phase 3 总耗时（核心瓶颈） |
| `Epsilon minimum` | 二分搜索得到的最小 ε |
| `LP calls` | 实际求解的 LP 数量 |
| `wall time per eps` | 各 ε 值的耗时分布（通常 ε=0.0 最慢） |
| `pre-filtered` | action pre-filter 跳过的无效检查数 |

## 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--coarse_resolution` | `coarse` | 粗糙 IMDP 分辨率 |
| `--fine_resolution` | `fine` | 精细 IMDP 分辨率 |
| `--eps_tol` | `1e-3` | ε 二分搜索精度 |
| `--n_jobs` | `-1` | 并行线程数，-1=全部CPU，1=串行 |
| `--seed` | `42` | 随机种子 |
| `--rebuild` | (flag) | 忽略缓存，强制重建 IMDP |

## 执行流程

```
Phase 1: 构建 IMDP_coarse + IMDP_fine   ~15s (首次)
Phase 2: 构建 f2c 映射                  ~2s  (首次)
         ↓
    存到 .cache_imdps/imdps_{coarse}_{fine}.pkl
         ↓
    后续运行直接加载缓存 → 秒级
         ↓
Phase 3: ε 二分搜索 (Algorithm 2)
  ├─ ε=1.0:  trivial case，不解 LP，秒级
  ├─ ε=0.0:  最耗时，大量 LP
  └─ 二分迭代: 逐步缩小 [lo, hi]，每次调用 Algorithm 2 固定点迭代
         ↓
    输出: ε_min, |R_final|, LP calls, wall time
```

## 缓存

- 路径: `.cache_imdps/imdps_{coarse}_{fine}.pkl`
- 不同分辨率组合各自独立缓存
- 删除 `.pkl` 文件或使用 `--rebuild` 强制重建
