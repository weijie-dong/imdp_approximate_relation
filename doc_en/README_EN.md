# `doc_en/` Document Index (by topic)

> This index categorizes all docs under `doc_en/` by topic, with status tags, for easy lookup.
> Tags: ✅ current ｜ ⚠️ deprecated/untrustworthy ｜ 📜 historical ｜ 🆕 new (post 2026-07 lazy→tiered).
> (中文版：`README.md`)

> **Colleagues start here**: §1 (onboarding) + §2 (if you ever used `lazy`).
> **Large-scale runs on a cluster**: §8.

---

## 1. Start here

| File | What | Status |
|---|---|---|
| `email_draft.md` | Handoff email (repo URL + entry pointers) | ✅ |
| `collaborator_guide.md` | Quick start (env, smoke test, demo pipeline) | ✅ (lazy-deprecation banner on top) |
| `step_workflow.md` | Full 3-step pipeline walkthrough (build / ε-search / validate) | ✅ |
| `project_overview.md` | High-level architecture: what the original framework does, what we added, full pipeline diagram | ✅ |
| `migration_guide.md` | **File manifest** for porting to a new machine (13 required + 5 optional) | ✅ (lazy-deprecation banner on top) |

## 2. ⚠️ If you used `method='lazy'` (must read)

| File | What | Status |
|---|---|---|
| `UPDATE_lazy_to_tiered_EN.md` | 🆕 **Clarification**: why lazy is unsound → what changed → where to look → what to run now | ✅🆕 |
| `lazy_enum_review/lazy_enum_soundness_analysis.md` | Full proof: dual upper bound certifies infeasibility only, never feasibility | ✅ |
| `lazy_enum_review/STATUS_AND_ROADMAP.md` §2.2 | Defect list + unrepairability | ✅ |

> Any `ε_min`/`R` from `lazy` is not a valid result — re-run with `corner`/`tiered`.

## 3. Methods (the `method=` choice)

| method | Doc | sound? | Status |
|---|---|---|---|
| `corner` | `Competitive_Approximate_Relation_Computation.md` (Algorithm 2 + §3 barrier) | ✅ sound+complete (exact baseline) | ✅ |
| `tiered` | `new_running_example/design.md` (tiered design + Tier 1/1.25/1.5/3 + K_LBSTAR=8) | ✅ sound+complete (exact acceleration) | ✅🆕 |
| `lazy` | `lazy_enum_and_optimizations.md` (original cutting-plane doc) | ❌ unsound | ⚠️ deprecated |
| `dual` | `interval_coupling_dual.md` (interval-arithmetic coupling via LP duality) | ❌ experimental/untrustworthy | ⚠️ deprecated |

> Use `corner` or `tiered`; do not use `lazy`/`dual`.

## 4. Theory

| File | What | Status |
|---|---|---|
| `lazy_enum_review/formal_lower_bound_theorem.md` | Proven bracket `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB` + sound certificates + gap characterization | ✅ |
| `Competitive_Approximate_Relation_Computation.md` | Algorithm 2 (competitive ∀a2∃a1) + §3: LP duality cannot eliminate corner enumeration in the worst case | ✅ |

## 5. Architecture & pipeline

| File | What |
|---|---|
| `project_overview.md` | High-level: original framework modules + roles of our new `core/approx_sim/` modules + full pipeline diagram |
| `step_workflow.md` | 3-step pipeline detail (step1 build / step2 ε-search / step3 validate) |
| `migration_guide.md` | File manifest (for porting) |

> The **execution flow & architecture of `tiered`** is in `new_running_example/design.md`
> (§2 tiered design, §3 integration into `compute_approx_sim`). *(Chinese; execution needs only
> `cluster_handoff_EN.md` which is English.)*

## 6. Running examples (paper illustration)

### 6a. Paper running example (M1/M2, original)
| File | What |
|---|---|
| `running_example/example_description.md` | M1/M2 definition + corners + coupling LP hand-derivation (cooperative ε=0 removes p1p2 / competitive ε=0 keeps) |
| `running_example/new_model.md` | Same case, manual derivation + reproduction (fixed intervals; cooperative ε=0 / competitive ε≈0.2) |
| `running_example/verification_plan.md` | Verification plan for that case |
| `running_example/verification_record.md` | Verification record |
| `running_example/lower_bound_validation_and_example_assessment.md` | Lower-bound validation + example assessment |
| `running_example/paper_ready_running_example_table.md` | Paper-ready tables |
| `running_example/k1_3_subexample.py` | k1=3 sub-example (6 corners, 8 subsets, per-subset table) |
| `running_example/validate_lower_bound_running_example.py` | Lower-bound / bracket validation script |

### 6b. 🆕 New running example (tweaked δ, non-trivial for both semantics)
| File | What | Status |
|---|---|---|
| `new_running_example/design.md` | Tweaked δ (comp/coop both ε_min=0.1) + tiered design + small-model validation + 2D findings | ✅🆕 |
| `new_running_example/run_running_example_pipeline.py` | Three-way cross-validation script (tiered==corner==hand-calc) | ✅🆕 |

> Difference: 6a's original is competitive-trivial (ε_min=0); 6b's tweak makes both semantics
> non-trivial (ε_min=0.1) and actually runs the `compute_approx_sim` pipeline.

## 7. Validation results

| File | What | Status |
|---|---|---|
| `new_running_example/design.md` §10–§12 | running example three-way + Test1D 15→5/21→7 full-ε + per-sub-pair soundness + 2D findings | ✅🆕 |
| `lazy_enum_review/step2_large_scale_results.md` | Sound-bounds measurement on 4 Test1D scales (bracket + residual fractions) | ✅ |
| `running_example/lower_bound_validation_and_example_assessment.md` | running example lower-bound validation | ✅ |
| `paper_examples_verification.md` | Verification of paper Figure-2 examples — **uses `lazy`** | ⚠️ results invalid; re-verify with corner/tiered |

## 8. Large-scale / cluster runs

| File | What | Status |
|---|---|---|
| `new_running_example/cluster_handoff_EN.md` | 🆕 **Cluster run book (English)**: commands, expected, PASS criteria, known behavior | ✅🆕 |
| `new_running_example/cluster_handoff.md` | Same (Chinese) | ✅🆕 |

## 9. Historical review (`lazy_enum_review/`)

The full reasoning trail of the lazy deprecation (consult as needed; mostly Chinese):

| File | What | Status |
|---|---|---|
| `lazy_enum_review/STATUS_AND_ROADMAP.md` | Index/tracker for that subfolder + 7-step plan + §2.6 "ε is the output" re-framing | ✅ |
| `lazy_enum_review/lazy_enum_bugs_and_theory_review.md` | lazy bug list + theory questions Q1/Q2/Q3 | 📜 historical |
| `lazy_enum_review/lazy_enum_soundness_analysis.md` | Why lazy is unsound (core argument) | ✅ |
| `lazy_enum_review/lazy_enum_fix_and_alternatives.md` | Fix plan + alternatives (with ⚠️CORRECTION banner retracting (b)) | ✅ (with corrections) |
| `lazy_enum_review/lazy_enum_lower_bound_theory.md` | Informal lower-bound theory | ⚠️ superseded by `formal_lower_bound_theorem.md` |
| `lazy_enum_review/formal_lower_bound_theorem.md` | Rigorous theorem (Lemma-Thm-Proof + §6 corrections) | ✅ |
| `lazy_enum_review/step2_large_scale_results.md` | Test1D bounds measurement | ✅ |

## 10. Experiment records & paper artifacts

| File | What | Status |
|---|---|---|
| `log.md` | Past run log (2026-06, Ubuntu, env/results) | 📜 historical |
| `algorithm2_timing_benchmark.md` | Algorithm 2 timing benchmark (incl. 50.8h case context) | 📜 historical |
| `experiment_5act_vs_7act.md` | 5-action vs 7-action experiment record | 📜 historical |
| `running_example/scalable_test_record.md` | Test1D scale-sweep record | 📜 historical |
| `running_example/paper_ready_running_example_table.md` | Paper-ready tables | ✅ |

---

## Recommended reading order (new colleague)

1. `email_draft.md` → `collaborator_guide.md` (env + smoke test)
2. `UPDATE_lazy_to_tiered_EN.md` (**method choice**: use corner/tiered, not lazy)
3. `project_overview.md` (architecture) → `step_workflow.md` (pipeline)
4. Large-scale: `new_running_example/cluster_handoff_EN.md`
5. Deep theory/history: `lazy_enum_review/STATUS_AND_ROADMAP.md` (that subfolder's index)

## Code entry points (not in doc_en/, but relevant)

- `method='corner'|'tiered'`: `core/approx_sim/algorithm.py` (`compute_approx_sim`) + `epsilon_search.py` (`compute_min_epsilon`)
- New tiered check: `core/approx_sim/coupling_tiered.py` (`K_LBSTAR=8`) + `coupling_bounds.py` (sound bounds)
- CLIs: `compare_methods.py` (corner vs tiered), `check_tiered_soundness.py` (per-sub-pair),
  `time_algorithm2.py --method tiered` (2D), `run_pipeline.py` (YAML pipeline)
