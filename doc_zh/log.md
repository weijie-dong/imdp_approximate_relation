# IMDP Approximate Simulation — 运行记录

## 环境信息

| 项目 | 值 |
|------|-----|
| 日期范围 | 2026-06-08 ~ 2026-06-14 |
| Git commit | `75bc0d7` — Add DoubleIntegrator model + fix corner enumeration correctness |
| OS | Ubuntu 22.04.5 LTS |
| Python | 3.13.13 |
| JAX | 0.9.2 |
| Conda env | `dyabstract` |

---

## Step 1: IMDP 构建记录

### DoubleIntegrator 3 动作 (u ∈ {-5, 0, 5})

| 配置 | 分辨率 | 网格 | 状态数 | V(s0) | V>0 | 构建耗时 | RVI耗时 | 总耗时 | 输出 |
|------|--------|------|--------|-------|-----|----------|---------|--------|------|
| `di_coarse` | coarse | 7×7 | 49 | 5.19e-08 | true | 6.2s | 0.8s | 7.1s | `output/di_coarse/` |
| `di_medium` | medium | 14×14 | 196 | 0.314 | true | 7.8s | 14.2s | 22.0s | `output/di_medium/` |
| `di_fine` | fine | 21×21 | 441 | 0.373 | true | 8.0s | 22.5s | 30.5s | `output/di_fine/` |
| `di_medium_x2` | medium_x2 | 28×28 | 784 | 0.464 | true | 8.3s | 32.6s | 41.0s | `output/di_medium_x2/` |
| `di_fine_x2` | fine_x2 | 42×42 | 1,764 | 0.861 | true | 8.9s | 25.3s | 34.2s | `output/di_fine_x2/` |

### DoubleIntegrator 多动作变体

| 配置 | 分辨率 | 网格 | 动作数 | 状态数 | V(s0) | V>0 | 构建耗时 | RVI耗时 | 总耗时 | 输出 |
|------|--------|------|--------|--------|-------|-----|----------|---------|--------|------|
| `di_medium_5act` | medium_5act | 14×14 | 5 | 196 | **0.688** | true | 8.4s | 9.0s | 17.4s | `output/di_medium_5act/` |
| `di_fine_7act` | fine_7act | 21×21 | 7 | 441 | **0.995** | true | 8.1s | 1.6s | 9.7s | `output/di_fine_7act/` |

### 关键观察

- **3 动作 V 值普遍偏低**: coarse ~0, medium 0.31, fine 0.37。3 个离散动作不足以表达有效的 reach-avoid 策略
- **coarse V≈0 但仍标记 viable**: V(s0)=5.19e-08，数值上 > 1e-9 阈值，但实际策略不可用。在实际使用中 coarse 不适合作为粗 IMDP
- **fine_x2 V=0.861 意外高于 fine**: 更密的网格反而给 V 带来了提升——精细划分减少了概率区间的不确定性
- **多动作显著提升 V**: 5 动作 medium V=0.688 (2.2×提升)，7 动作 fine V=0.995 (2.7×提升)，策略表达能力是瓶颈而非网格精度
- **7 动作 fine RVI 收敛极快**: 1.6s，远快于同网格 3 动作的 22.5s——更细的动作空间使策略迭代更容易找到最优解

---

## Step 2+3: 成对分析记录

### demo — coarse→coarse (49→49, 相同网格)

| 项 | 值 |
|----|-----|
| 日期 | 2026-06-09 |
| 精细 IMDP | `output/di_coarse/imdp.pkl` |
| 粗糙 IMDP | `output/di_coarse/imdp.pkl` |
| f2c 映射 | 严格 1:1 (相同网格) |

**ε 二分搜索:**

| ε | 可行 | \|R\| | LP 调用 | 耗时 |
|---|--------|------|---------|------|
| 1.0 | yes | 49 | 1,190 | 0.8s |
| 0.0 | yes | 49 | 1,771 | 12.2s |

**结果:** ε_min = **0.0** (精确仿真)

**RVI + 策略迁移 + MC 验证:**

| 指标 | 值 |
|------|-----|
| V_coarse(s0) | 5.19e-08 |
| 经验满足概率 | 0.9794 |
| 理论下界 | 5.19e-08 |
| Degradation | 0.0 |
| Bound holds | **True** |
| MC 耗时 | 127.4s |

**解读:** 相同网格存在精确仿真关系 (ε=0)。MC 仿真 97.9% 到达目标，远高于理论下界（接近 0）。说明真实系统可控性很好，但粗抽象太保守导致 V 值低估。

---

### di_medium_fine — medium→fine (196→441, 非整数比 1.5×)

**状态:** 尚未运行

---

### di_medium_5act_fine_7act — 推荐案例 (196→441, 5act→7act)

**状态:** 已完成，但近似仿真关系不成立

**日期**: 2026-06-12 ~ 2026-06-14

详细分析见 [experiment_5act_vs_7act.md](experiment_5act_vs_7act.md)。

| 指标 | 值 |
|------|-----|
| ε_min | **0.999** (几乎 trivial) |
| ε 可用的临界区间 | [0.999, 1.0] |
| \|R_initial\| | 784 对 |
| ε ≤ 0.998 时 |R|| **0** (全部坍塌) |
| Step 2 总耗时 | 182,767s (~50.8h) |
| V_coarse(s0) | 0.6879 |
| 经验满足概率 | 1.0000 |
| 理论下界 | 0.0000 |
| Degradation | 1.0000 |
| Bound holds | True (但无意义) |

**结论:** 5 动作 vs 7 动作的动作集合不匹配导致 ε → 1。bound 形式上成立但 degradation=1.0 使理论下界为 0，信息量为零。建议使用相同动作集合（方案 1）。

---

## 汇总

### 所有 IMDP 构建总览

```
名称            网格    动作  V(s0)    耗时    V>0
────            ────    ──   ─────    ────    ───
di_coarse       7×7      3   ~0       7.1s    ✓
di_medium       14×14    3   0.314   22.0s    ✓
di_fine         21×21    3   0.373   30.5s    ✓
di_medium_x2    28×28    3   0.464   41.0s    ✓
di_fine_x2      42×42    3   0.861   34.2s    ✓
di_medium_5act  14×14    5   0.688   17.4s    ✓
di_fine_7act    21×21    7   0.995    9.7s    ✓
```

### Pair 分析总览

```
名称                              粗→细             ε_min   bound   状态
────                              ────              ─────   ─────   ──
demo                             coarse→coarse      0.0     true    ✓ 完成
di_medium_5act_fine_7act         medium_5act→fine_7act 0.999 true (trivial) ✗ 失败
di_medium_fine                   medium→fine          —       —      ○ 待运行
```

### 推荐运行顺序

```bash
# 1. 快速验证 (已完成)
python run_pipeline.py pair --config configs/approx_sim.yaml demo

# 2. 方案 1: 统一 7 动作 (下一步推荐)
#    先构建 di_medium_7act，然后创建 di_medium_7act → di_fine_7act pair
python steps/step1_build_imdp.py \
    --model DoubleIntegratorApproxSim --resolution medium_7act \
    --output output/di_medium_7act

# 3. 方案 4 验证: 整数比 + 相同动作
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine_x2

# 4. 非整数比 + 相同动作
python run_pipeline.py pair --config configs/approx_sim.yaml di_medium_fine
```
