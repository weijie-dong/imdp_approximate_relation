# 澄清：`method='lazy'` 不 sound —— 请改用 `method='tiered'`（或 `corner`）

> **给此前拿到过本代码、并使用过 `method='lazy'` 的同事。**
>
> 如果你是在 2026-07 之前拿到本仓库、并用 `method='lazy'`（切割平面法）求速度，请先读本文。
> **`lazy` 方法已弃用（不 sound）。** 请改用 `method='corner'`（精确基线）或新的
> `method='tiered'`（sound 加速）。环境、管线、文件清单（`migration_guide.md` 等）**均未变**，
> 变的只是"求耦合可行性时用哪个 method"。

中文版澄清；英文同事请看 [`UPDATE_lazy_to_tiered_EN.md`](UPDATE_lazy_to_tiered_EN.md)（完整英文版），
集群运行见 `new_running_example/cluster_handoff_EN.md`。

---

## 1. `method='lazy'` 哪里错了

`lazy` 切割平面检查（原始说明：`lazy_enum_and_optimizations.md`）当初为避免枚举全部 2^k1 个
fine 角而引入。它的 **True-path**（"分离收敛 ⇒ 所有角可行"）**不 sound 且无法修补**：

- 耦合 LP 的对偶给出的是逐角可行裕度 `g` 的**上界**。上界只能证**不可行**，**永远不能证可行**。
  `lazy` 把它当成可行性证书 ⟹ 可能把**实际不可行的对判成可行**（false-feasible）
  ⟹ 最终的 `ε` / `R` **不可信**。
- 另有两个 bug：(A) `_solve_separation_lp` 用了 `reversed(order)`，返回的是**最不可能违反**的角；
  (B) 一个 `max_iter` 收敛 break 被误标。
- 这与我们自己的理论一致（`Competitive_Approximate_Relation_Computation.md` §3：LP 对偶在最坏
  情形下不能消除角枚举）。

完整论证：`lazy_enum_review/lazy_enum_soundness_analysis.md` + `lazy_enum_review/STATUS_AND_ROADMAP.md` §2.2。

> **后果**：凡是用 `method='lazy'` 跑出的 `ε_min` / `R`，都不能作为正式结果。需用 `corner` 或
> `tiered` 重跑。

## 2. 我们做了什么改动（新的 `method='tiered'`）

一个 **sound + complete** 的替代，**绝不弱于** Theorem V.3 角枚举：

- **Tier 1（LP-free）** `UB` / `LB_min`：`UB < 1−ε` ⟹ 不可行；`LB_min ≥ 1−ε` ⟹ 可行（弱）。
- **Tier 1.25（1 LP）** 最难角探针（sound 的不可行见证）。
- **Tier 1.5（1 LP）** `LB*`（最紧的 sound 下界）：`LB* ≥ 1−ε` ⟹ 可行。
- **Tier 3（精确）** 全角枚举 —— **与 `method='corner'` 逐字节相同**。

`tiered == corner` 在残差上 *by construction* 成立；bounds 只在 corner 也会给出同样答案处捷径。
k1 自适应（`K_LBSTAR=8`）：小 k1 用全分层；大 k1 跳过 LB\*+探针（大 k1 紧 ε 下 LB\* LP 是负债）。
已在小模型上验证 **无 bug**（Test1D 15→5 / 21→7 全 ε 搜索 + 逐 sub-pair 对精确 g；running example
三方互证）——0 mismatch、0 false-feasible。

新增/改动文件：
- 新 `core/approx_sim/coupling_tiered.py`、`core/approx_sim/coupling_bounds.py`（已证 sound bounds）。
- `core/approx_sim/algorithm.py`：加 `method='tiered'` 臂。
- `time_algorithm2.py`、`compare_methods.py`：`--method tiered` / `'tiered'` 选项。
- 新 `check_tiered_soundness.py`、`doc_en/new_running_example/run_running_example_pipeline.py`。
- `method='lazy'` 代码**保留但弃用，勿用**（`method='dual'` 同样不可信，亦勿用）。

## 3. 去哪查（架构 / 执行流程 / 理论）

| 你要找 | 文件 |
|---|---|
| tiered 的架构与执行流程 | `new_running_example/design.md` |
| 集群运行命令（copy-paste 可执行） | `new_running_example/cluster_handoff_EN.md`（§4） |
| 理论（已证括号 `LB_min ≤ LB* ≤ g ≤ UB`） | `lazy_enum_review/formal_lower_bound_theorem.md` |
| lazy 为何不 sound（完整） | `lazy_enum_review/lazy_enum_soundness_analysis.md` |
| Algorithm 2 / §3 屏障 | `Competitive_Approximate_Relation_Computation.md` |
| 原管线 / 文件清单（未变） | `project_overview.md`、`step_workflow.md`、`migration_guide.md` |
| 小模型验证结果 | `new_running_example/design.md` §10–§12 |

## 4. 现在该跑什么

- **用 `method='corner'`（精确）或 `method='tiered'`（加速）。** 二者皆 sound。**勿用 `lazy`（或 `dual`）**。
- 命令见 `new_running_example/cluster_handoff_EN.md` §4。冒烟测试：
  `python doc_en/new_running_example/run_running_example_pipeline.py`（应打印三方互证 PASS）。
- 大规模：corner 与 tiered **串行**跑（都 `n_jobs=-1` 占满 CPU，并发会互相饿慢），核对两者
  `epsilon_min` / `|R_final|` 一致。

---

## EN summary (for English-reading colleagues)

The `method='lazy'` cutting-plane check you may have used is **unsound (deprecated)**: its dual is
an *upper* bound on the per-corner margin g, which can certify infeasibility only — never feasibility
— so it can produce **false-feasible** pairs and untrustworthy ε/R. Details:
`lazy_enum_review/lazy_enum_soundness_analysis.md`. Use `method='corner'` (exact) or the new
`method='tiered'` (sound+complete acceleration; Tier 3 == corner). Architecture/run flow:
`new_running_example/design.md`; cluster commands: `new_running_example/cluster_handoff_EN.md` §4;
theory: `lazy_enum_review/formal_lower_bound_theorem.md`. Small models verified bug-free
(Test1D 15→5/21→7 + running example, 0 mismatch). Re-run any `lazy` results with `corner`/`tiered`.
