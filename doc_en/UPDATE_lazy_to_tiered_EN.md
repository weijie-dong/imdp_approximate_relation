# Clarification: `method='lazy'` is unsound — use `method='tiered'` (or `corner`)

> **For colleagues who received this codebase before July 2026 and used `method='lazy'` for speed.**
>
> The `lazy` cutting-plane method is **deprecated (unsound)**. Use `method='corner'` (exact baseline)
> or the new `method='tiered'` (sound acceleration). Everything else (environment, pipeline, file
> manifest in `migration_guide.md`) is **unchanged** — only the "which `method=` to use for the
> coupling check" has changed.

(中文版：`UPDATE_lazy_to_tiered.md`)

---

## 1. What is wrong with `method='lazy'`

The `lazy` cutting-plane check (original doc: `lazy_enum_and_optimizations.md`) was introduced to
avoid enumerating all 2^k1 fine corners. Its **True-path** ("separation converged ⇒ all corners
feasible") is **unsound and unrepairable**:

- The coupling-LP **dual** gives an **upper bound** on the per-corner feasibility margin `g`. An
  upper bound can certify **infeasibility** only — it can **never** certify feasibility. The `lazy`
  method misuses it as a feasibility certificate ⟹ it can declare pairs **feasible that are
  actually infeasible** (false-feasible) ⟹ the final `ε` / `R` are **not trustworthy**.
- Two further bugs: (A) `_solve_separation_lp` used `reversed(order)`, returning the corner that
  *maximizes* `pᵀα` (least likely to violate) instead of minimizing; (B) a `max_iter` convergence
  break was mislabeled as `max_iter`.
- This matches the project's own theory (§3 of `Competitive_Approximate_Relation_Computation.md`):
  LP duality cannot eliminate corner enumeration in the worst case.

Full argument: `lazy_enum_review/lazy_enum_soundness_analysis.md` + `lazy_enum_review/STATUS_AND_ROADMAP.md` §2.2.

> **Consequence**: any `ε_min` / `R` produced with `method='lazy'` is **not a valid result**.
> Re-run with `corner` or `tiered`.

## 2. What we changed (the new `method='tiered'`)

A **sound + complete** replacement that is **never less rigorous** than Theorem V.3 corner
enumeration:

- **Tier 1 (LP-free)** `UB` / `LB_min`: `UB < 1−ε` ⟹ INFEASIBLE (sound); `LB_min ≥ 1−ε` ⟹ FEASIBLE (weak).
- **Tier 1.25 (1 LP)** hardest-corner probe — a sound infeasible witness (the feasible-c1 set is
  convex and P1 = conv(corners), so if any point of P1 is infeasible, some corner is).
- **Tier 1.5 (1 LP)** `LB*` (tightest sound lower bound): `LB* ≥ 1−ε` ⟹ FEASIBLE.
- **Tier 3 (exact)** full fine-corner enumeration, `check_coupling` each — **byte-identical to
  `method='corner'`**.

`tiered == corner` by construction on the residual; the bounds only shortcut cases corner would
decide the same way. k1-adaptive (`K_LBSTAR=8`): small k1 uses all tiers; large k1 skips LB\*+probe
(the 2^k1-constraint LB\* LP is a liability at tight ε / large k1) — still sound + complete.

**Verified bug-free on small models**: Test1D 15→5 / 21→7 (full ε-search, `tiered == corner`, 0
iteration mismatches) + per-sub-pair vs exact `g` (0 false-feasible, 0 false-infeasible) + running
example three-way (tiered == corner == hand-calc). See `new_running_example/design.md` §10–§11.

New / changed files:
- new `core/approx_sim/coupling_tiered.py`, `core/approx_sim/coupling_bounds.py` (proven sound bounds).
- `core/approx_sim/algorithm.py`: added the `method='tiered'` arm.
- `time_algorithm2.py`, `compare_methods.py`: `--method tiered` / `'tiered'` option.
- new `check_tiered_soundness.py`, `doc_en/new_running_example/run_running_example_pipeline.py`.
- `method='lazy'` code is **left in place but deprecated — do not use** (`method='dual'` is also
  untrustworthy; do not use).

## 3. Where to find things

| You need | File |
|---|---|
| Architecture & execution flow of `tiered` | `new_running_example/design.md` |
| Cluster run commands (copy-paste) | `new_running_example/cluster_handoff_EN.md` (§4) |
| Theory (proven bracket `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB`) | `lazy_enum_review/formal_lower_bound_theorem.md` |
| Why `lazy` is unsound (full) | `lazy_enum_review/lazy_enum_soundness_analysis.md` |
| Algorithm 2 / §3 barrier | `Competitive_Approximate_Relation_Computation.md` |
| Original pipeline / file manifest (unchanged) | `project_overview.md`, `step_workflow.md`, `migration_guide.md` |
| Small-model validation results | `new_running_example/design.md` §10–§12 |

> Note: `design.md` and the `lazy_enum_review/` docs are in Chinese. For execution you only need
> `cluster_handoff_EN.md` (English); for theory, `formal_lower_bound_theorem.md` and
> `Competitive_Approximate_Relation_Computation.md` are in English. Ask the author if you need an
> English translation of `design.md`.

## 4. What to run now

- **Use `method='corner'` (exact) or `method='tiered'` (acceleration).** Both sound. **Never
  `lazy` (or `dual`).**
- Commands: `new_running_example/cluster_handoff_EN.md` §4. Smoke test:
  ```bash
  python doc_en/new_running_example/run_running_example_pipeline.py   # three-way PASS
  ```
- For large cases, run `corner` and `tiered` **sequentially** (both use `n_jobs=-1` = all CPUs;
  running them concurrently starves both) and check that `epsilon_min` and `|R_final|` match.
