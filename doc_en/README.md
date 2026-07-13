# `doc_en/` 文档索引（按主题分类）

> 📗 English index: `README_EN.md`（for English-reading colleagues）。
>
> 本索引把 `doc_en/` 下所有文档**按主题分门别类**，标注状态，方便查阅。
> 标签：✅当前 ｜ ⚠️弃用/不可信 ︱ 📜历史 ︱ 🆕新增（2026-07 lazy→tiered 之后）。

> **拿到代码的同事先读**：§1（入门）+ §2（如果你用过 `lazy`）。
> **集群跑大规模**：§8。

---

## 1. 入门（Start here）

| 文件 | 内容 | 状态 |
|---|---|---|
| `email_draft.md` | 发给同事的交接邮件（仓库地址 + 入口指引） | ✅ |
| `collaborator_guide.md` | 同事快速上手（环境、冒烟测试、demo 管线） | ✅（顶部有 lazy 弃用提示） |
| `step_workflow.md` | 完整 3 步管线 walkthrough（build / ε-search / validate） | ✅ |
| `project_overview.md` | 项目高层架构：原框架做了什么、我加了什么、完整管线图 | ✅ |
| `migration_guide.md` | 移植到新机器的**文件清单**（13 必需 + 5 可选） | ✅（顶部有 lazy 弃用提示） |

## 2. ⚠️ 如果你用过 `method='lazy'`（必读）

| 文件 | 内容 | 状态 |
|---|---|---|
| `UPDATE_lazy_to_tiered.md` | 🆕 **澄清文档**：lazy 为何不 sound → 改了什么 → 去哪查 → 现在该跑什么 | ✅🆕 |
| `lazy_enum_review/lazy_enum_soundness_analysis.md` | 完整论证：对偶上界只能证不可行、不能证可行 | ✅ |
| `lazy_enum_review/STATUS_AND_ROADMAP.md` §2.2 | lazy 的缺陷清单 + 不可修补性 | ✅ |

> 凡用 `lazy` 跑出的 `ε_min`/`R` 都不可作正式结果，需用 `corner`/`tiered` 重跑。

## 3. 方法（`method=` 的选择）

| method | 文档 | sound？ | 状态 |
|---|---|---|---|
| `corner` | `Competitive_Approximate_Relation_Computation.md`（含 Algorithm 2 + §3 屏障） | ✅ sound+complete（精确基线） | ✅ |
| `tiered` | `new_running_example/design.md`（分层设计 + Tier 1/1.25/1.5/3 + K_LBSTAR=8） | ✅ sound+complete（精确加速） | ✅🆕 |
| `lazy` | `lazy_enum_and_optimizations.md`（原始切割平面法说明） | ❌ 不 sound | ⚠️弃用 |
| `dual` | `interval_coupling_dual.md`（区间算术耦合 LP 对偶） | ❌ 实验性/不可信 | ⚠️弃用 |

> 用 `corner` 或 `tiered`；勿用 `lazy`/`dual`。

## 4. 理论（Theory）

| 文件 | 内容 | 状态 |
|---|---|---|
| `lazy_enum_review/formal_lower_bound_theorem.md` | 已证括号 `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB` + sound 证书 + gap 刻画 | ✅ |
| `Competitive_Approximate_Relation_Computation.md` | Algorithm 2（competitive ∀a2∃a1）+ §3：LP 对偶最坏情形不能消除角枚举 | ✅ |

## 5. 架构与管线

| 文件 | 内容 |
|---|---|
| `project_overview.md` | 高层架构：原框架模块 + 我新增的 `core/approx_sim/` 各模块角色 + 完整管线图 |
| `step_workflow.md` | 3 步管线详解（step1 build / step2 ε-search / step3 validate） |
| `migration_guide.md` | 文件清单（移植用） |

> tiered 的**执行流程与架构**另见 `new_running_example/design.md`（§2 分层设计、§3 集成进 `compute_approx_sim`）。

## 6. Running example（论文示例 / 直观说明）

论文有两个层级的 running example 生态：

### 6a. 论文 running example（M1/M2，原始）
| 文件 | 内容 |
|---|---|
| `running_example/example_description.md` | M1/M2 定义 + 角点 + 耦合 LP 手推（cooperative ε=0 删 p1p2 / competitive ε=0 留） |
| `running_example/new_model.md` | 同一 case 的手推+复现（固定区间，cooperative ε=0 / competitive ε≈0.2） |
| `running_example/verification_plan.md` | 该 case 的验证计划 |
| `running_example/verification_record.md` | 验证记录 |
| `running_example/lower_bound_validation_and_example_assessment.md` | 下界验证 + example 评估 |
| `running_example/paper_ready_running_example_table.md` | 论文用表（Tables/Figure 文本） |
| `running_example/k1_3_subexample.py` | k1=3 子例（6 角、8 子集，逐子集表） |
| `running_example/validate_lower_bound_running_example.py` | 下界/bracket 验证脚本 |

### 6b. 🆕 新 running example（微调 δ，两种语义都不平凡）
| 文件 | 内容 | 状态 |
|---|---|---|
| `new_running_example/design.md` | 微调 δ（comp/coop 均 ε_min=0.1）+ tiered 设计 + 小模型验证 + 2D 发现 | ✅🆕 |
| `new_running_example/run_running_example_pipeline.py` | 三方互证脚本（tiered==corner==手算） | ✅🆕 |

> 区别：6a 的原例 competitive 平凡（ε_min=0）；6b 微调 δ 后两种语义都不平凡（ε_min=0.1），
> 且 6b 真正走 `compute_approx_sim` 管线。

## 7. 验证结果（Validation results）

| 文件 | 内容 | 状态 |
|---|---|---|
| `new_running_example/design.md` §10–§12 | running example 三方互证 + Test1D 15→5/21→7 全 ε + 逐 sub-pair soundness + 2D 性能发现 | ✅🆕 |
| `lazy_enum_review/step2_large_scale_results.md` | Test1D 四规模的 sound bounds 实测（bracket + 残差比例） | ✅ |
| `running_example/lower_bound_validation_and_example_assessment.md` | running example 下界验证 | ✅ |
| `paper_examples_verification.md` | 论文 Figure 2 例子的验证 —— **用了 lazy** | ⚠️结果不可信，需用 corner/tiered 重验 |

## 8. 大规模 / 集群运行

| 文件 | 内容 | 状态 |
|---|---|---|
| `new_running_example/cluster_handoff_EN.md` | 🆕 **集群执行手册（英文）**：命令、预期、判 PASS、已知行为 | ✅🆕 |
| `new_running_example/cluster_handoff.md` | 同上（中文） | ✅🆕 |

## 9. 历史评审（`lazy_enum_review/`）

lazy 弃用过程的完整推理记录（按需查阅）：

| 文件 | 内容 | 状态 |
|---|---|---|
| `lazy_enum_review/STATUS_AND_ROADMAP.md` | 该子目录的索引/tracker + 7 步计划 + §2.6 "ε 是输出"重定位 | ✅ |
| `lazy_enum_review/lazy_enum_bugs_and_theory_review.md` | lazy bug 清单 + 理论问题 Q1/Q2/Q3 | 📜历史 |
| `lazy_enum_review/lazy_enum_soundness_analysis.md` | lazy 为何不 sound（核心论证） | ✅ |
| `lazy_enum_review/lazy_enum_fix_and_alternatives.md` | 修复方案 + 备选（含 ⚠️CORRECTION 横幅，撤回 (b)） | ✅（带订正） |
| `lazy_enum_review/lazy_enum_lower_bound_theory.md` | 非正式下界理论 | ⚠️被 formal_lower_bound_theorem.md 取代 |
| `lazy_enum_review/formal_lower_bound_theorem.md` | 严格定理（Lemma-Thm-Proof + §6 订正） | ✅ |
| `lazy_enum_review/step2_large_scale_results.md` | Test1D bounds 实测 | ✅ |

## 10. 实验记录与论文产物

| 文件 | 内容 | 状态 |
|---|---|---|
| `log.md` | 过往 run 记录（2026-06，Ubuntu，环境/结果） | 📜历史 |
| `algorithm2_timing_benchmark.md` | Algorithm 2 计时基准（含 50.8h 案背景） | 📜历史 |
| `experiment_5act_vs_7act.md` | 5 动作 vs 7 动作实验记录 | 📜历史 |
| `running_example/scalable_test_record.md` | Test1D 规模扫描记录 | 📜历史 |
| `running_example/paper_ready_running_example_table.md` | 论文用表 | ✅ |

---

## 推荐阅读顺序（新同事）

1. `email_draft.md` → `collaborator_guide.md`（环境 + 冒烟）
2. `UPDATE_lazy_to_tiered.md`（**方法选择**：用 corner/tiered，勿用 lazy）
3. `project_overview.md`（架构）→ `step_workflow.md`（管线）
4. 跑大规模：`new_running_example/cluster_handoff_EN.md`
5. 深入理论/历史：`lazy_enum_review/STATUS_AND_ROADMAP.md`（该子目录索引）

## 代码入口（不在 doc_en/，但相关）

- `method='corner'|'tiered'`：`core/approx_sim/algorithm.py`（`compute_approx_sim`）+ `epsilon_search.py`（`compute_min_epsilon`）
- 新分层检查：`core/approx_sim/coupling_tiered.py`（`K_LBSTAR=8`）+ `coupling_bounds.py`（sound bounds）
- 命令行：`compare_methods.py`（corner vs tiered）、`check_tiered_soundness.py`（逐 sub-pair）、
  `time_algorithm2.py --method tiered`（2D）、`run_pipeline.py`（YAML 管线）
