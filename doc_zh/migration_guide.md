# 近似仿真功能移植指南

本文档描述如何将 IMDP 近似仿真（approximate simulation）新增功能以最小文件集的方式移植到另一台电脑的全新原始项目上。

## 前置条件

目标电脑上已有原始 IMDP synthesis 开源项目的克隆：

```bash
git clone <原始项目地址>
cd imdp-synthesis
```

## 第一步：基础环境安装

```bash
conda create -n dyabstract python=3.13
conda activate dyabstract
pip install -r requirements.txt
```

确认原始功能正常（可选）：

```bash
python Main_IMDP.py --model Test1D --solver jax
```

## 第二步：额外依赖

```bash
pip install cvxpy pyyaml
```

- `cvxpy`: 耦合 LP 求解器（Algorithm 2 核心）
- `pyyaml`: YAML 配置文件解析

## 第三步：移植文件

以下所有文件均从源电脑复制到目标电脑对应位置。复制时注意使用当前工作区的最新版本（部分文件有未提交的修改），不要用 git 提交版本。

### 3.1 新建目录

在目标电脑项目根目录下创建以下空目录：

```bash
mkdir -p core/approx_sim
mkdir -p steps
mkdir -p configs
```

### 3.2 核心算法模块（必须）

将以下文件复制到 `core/approx_sim/` 目录：

| 文件 | 作用 |
|------|------|
| `core/approx_sim/__init__.py` | 包初始化 |
| `core/approx_sim/algorithm.py` | Algorithm 2 不动点迭代（核心算法，**使用当前工作区版本**） |
| `core/approx_sim/corners.py` | 转移多面体角点枚举 |
| `core/approx_sim/coupling.py` | 耦合 LP 构建与求解 |
| `core/approx_sim/epsilon_search.py` | ε 二分搜索（**使用当前工作区版本**） |
| `core/approx_sim/mapping.py` | 细粒度→粗粒度状态映射（**使用当前工作区版本**） |
| `core/approx_sim/policy_transfer.py` | 策略从粗 IMDP 迁移到细 IMDP |

### 3.3 Benchmark 模型（必须）

将以下文件复制到 `benchmarks/` 目录：

| 文件 | 作用 |
|------|------|
| `benchmarks/DoubleIntegrator_approx_sim.py` | 双积分器模型（主要测试模型，**使用当前工作区版本**） |
| `benchmarks/Dubins3D_approx_sim.py` | Dubins3D 模型 |

### 3.4 修改原始文件（必须）

目标电脑上已存在 `benchmarks/__init__.py`，需要手动做两处修改。

**修改 1** — 在文件顶部的 import 区域添加两行：

```python
from benchmarks.Dubins3D_approx_sim import Dubins3DApproxSim
from benchmarks.DoubleIntegrator_approx_sim import DoubleIntegratorApproxSim
```

**修改 2** — 在 `create_model()` 函数的 `model_map` 字典末尾添加两项。找到类似以下的结构：

```python
model_map = {
    "Test1D": Test1D,
    "Pendulum": Pendulum,
    # ... 更多已有模型 ...
}
```

在其中添加：

```python
    "DoubleIntegratorApproxSim": DoubleIntegratorApproxSim,
    "Dubins3DApproxSim": Dubins3DApproxSim,
```

### 3.5 流水线脚本（推荐）

将以下文件复制到 `steps/` 目录：

| 文件 | 作用 |
|------|------|
| `steps/step1_build_imdps.py` | Step 1: 构建 IMDP + V>0 检测 |

将以下文件复制到 `configs/` 目录：

| 文件 | 作用 |
|------|------|
| `configs/approx_sim.yaml` | build / pair 的 YAML 配置 |

将以下文件复制到项目根目录：

| 文件 | 作用 |
|------|------|
| `run_pipeline.py` | 主入口脚本，支持 `build` 和 `pair` 子命令 |
| `steps/step2_epsilon_search.py` | Step 2: ε 二分搜索 |
| `steps/step3_validate.py` | Step 3: 策略迁移 + RVI + MC 验证 |

### 3.6 可选文件

| 文件 | 位置 | 说明 |
|------|------|------|
| `test_approx_sim_synthetic.py` | 项目根 | 小规模合成测试 (5→15 states, ~20s) |
| `time_algorithm2.py` | 项目根 | Algorithm 2 耗时测量 |
| `Main_ApproxSim.py` | 项目根 | 备用 CLI 入口 |
| `core/approx_sim/coupling_dual.py` | `core/approx_sim/` | LP 对偶形式（实验性） |

## 第四步：验证

### 4.1 冒烟测试

```bash
python test_approx_sim_synthetic.py
```

应在大约 20 秒内完成，输出 pass/fail。

### 4.2 构建单个 IMDP

```bash
python steps/step1_build_imdps.py \
    --model DoubleIntegratorApproxSim --resolution coarse \
    --output output/di_coarse
```

应输出 V(s0) 值和构建耗时，生成 `output/di_coarse/imdp.pkl`。

### 4.3 完整 demo 流水线

```bash
python run_pipeline.py pair --config configs/approx_sim.yaml demo
```

demo 使用 coarse→coarse（同网格 49→49），预期 ε_min = 0.0（精确仿真），约 150 秒完成。

### 4.4 更多验证

```bash
# 构建 medium + fine 并运行 pair
python steps/step1_build_imdps.py \
    --model DoubleIntegratorApproxSim --resolution medium \
    --output output/di_medium

python steps/step1_build_imdps.py \
    --model DoubleIntegratorApproxSim --resolution fine \
    --output output/di_fine

python steps/step2_epsilon_search.py \
    --imdp_coarse output/di_medium/imdp.pkl \
    --imdp_fine output/di_fine/imdp.pkl \
    --output output/di_medium_fine

python steps/step3_validate.py \
    --imdp_coarse output/di_medium/imdp.pkl \
    --imdp_fine output/di_fine/imdp.pkl \
    --eps output/di_medium_fine/eps.pkl \
    --output output/di_medium_fine
```

## 文件清单汇总

移植完成后，目标电脑新增/修改的文件如下：

```
imdp-synthesis/
├── configs/
│   └── approx_sim.yaml                    # 新增
├── core/
│   └── approx_sim/                        # 新增目录
│       ├── __init__.py
│       ├── algorithm.py
│       ├── corners.py
│       ├── coupling.py
│       ├── coupling_dual.py               # 可选
│       ├── epsilon_search.py
│       ├── mapping.py
│       └── policy_transfer.py
├── benchmarks/
│   ├── __init__.py                        # 修改（添加 2 个新模型注册）
│   ├── DoubleIntegrator_approx_sim.py     # 新增
│   └── Dubins3D_approx_sim.py             # 新增
├── steps/                                 # 新增目录
│   ├── step1_build_imdps.py
│   ├── step2_epsilon_search.py
│   └── step3_validate.py
├── run_pipeline.py                        # 新增
├── Main_ApproxSim.py                      # 可选
├── test_approx_sim_synthetic.py           # 可选
└── time_algorithm2.py                     # 可选
```

共计 **13 个必须文件** + **5 个可选文件**，修改 **1 个原始文件**。
