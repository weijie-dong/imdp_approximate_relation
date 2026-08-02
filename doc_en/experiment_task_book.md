# Case Study Experiment Task Book (cluster edition)

> **Purpose**: complete all experiment data for paper §VII (Case Study). This
> document is self-contained and is the single handoff to the colleague running
> the cluster.
> **Division of labour**: experiment design & paper writing (this document's
> author); cluster runs & data return (colleague).
> **Code repo**: https://github.com/weijie-dong/imdp_approximate_relation
>   - **Structured results-dumper** (the entry point for every run):
>     `run_experiment.py` — writes the §5 machine-readable schema per run.
>   - Other scripts: `compare_methods.py`, `compare_methods_cooperative.py`
>     (1D quick harnesses, stdout only), `per_pair_epsilon.py` (E2 ranking),
>     `check_tiered_soundness.py` (per-sub-pair soundness audit).
>   - Semantics switch: `--semantics {competitive,cooperative}`.

---

## Machine-readable results dumping (the contract)

Every E1–E7 run goes through `run_experiment.py`, which writes a per-run
directory `runs/<bench>_<nf>to<nc>__<sem>__<method>__<mode>__rep<i>/`:

```
├── run.log          # bisection probe trajectory (search) or fixed-point line
├── result.csv       # one row, §5 schema (see below)
├── R_final.txt      # sorted (s1,s2) pairs of the final relation
├── tier_counts.json # only for method=tiered: raw 7-label histogram + bucket pct
└── env.txt          # node / cpu / solver / git commit / timestamp
```

**Schema (result.csv, one row per run)**:
```
benchmark,n_fine,n_coarse,semantics,method,tol,rep,
epsilon_min,R_size,wall_time_s,lp_calls,
tier1_pct,tier125_15_pct,tier3_pct,
converged,probe_count,node,solver,commit
```

`lp_calls` is the TRUE total (summed across all fixed-point iterations and all
bisection probes), not just the last iteration. `tier*_pct` = `NA` for
method=corner. `converged` distinguishes a clean bisection convergence
(`hi-lo<=tol`) from a killed/incomplete run.

**Tier label → paper-Tier bucket** (the 7 `decided_by` literals from
`coupling_tiered._result`):
| paper Tier | labels |
|---|---|
| Tier 1 (LP-free) | `lbmin_feas`, `ub_infeas`, `trivial_eps_one` |
| Tier 1.25–1.5 (1-LP probe / LB*) | `probe_infeas`, `lbstar_feas` |
| Tier 3 (full corner enum = FCE) | `enum_feas`, `enum_infeas` |

`tier_counts.json` keeps the raw 7-label histogram *and* the bucketed pct.

### Typical commands

```bash
# 1D ε-search (E1/E3/E4), tiered, dumps schema
python run_experiment.py --model 1D --fine 35 --coarse 7 \
    --semantics competitive --method tiered --mode search --rep 1
# 1D FCE (corner) baseline
python run_experiment.py --model 1D --fine 35 --coarse 7 \
    --semantics competitive --method corner --mode search --rep 1
# 2D ε-search (E1), fine=441 (21×21), coarse=49 (7×7)
python run_experiment.py --model 2D --fine fine --coarse coarse \
    --semantics competitive --method tiered --mode search --rep 1
# E7 fixed-ε single-shot verification
python run_experiment.py --model 1D --fine 15 --coarse 5 \
    --semantics competitive --method tiered --mode fixed --epsilon 0.005 --rep 1
# cooperative (E3)
python run_experiment.py --model 1D --fine 15 --coarse 5 \
    --semantics cooperative --method tiered --mode search --rep 1
```

⚠️ `tol` default is `--eps_tol 1e-3` (meets the spec without being set).
Run 3 reps by looping `--rep 1/2/3`; each writes one `result.csv` row.

### Name mapping (code ↔ paper)
- **1D-SI** = code model `Test1D` (single integrator), 1D, n=1. Built by
  `run_experiment.py --model 1D --fine <n_cells>` (cell count, e.g. 15/35/51).
- **2D-DI** = code model `DoubleIntegratorApproxSim` (double integrator), 2D.
  Built by `--model 2D --fine <resolution>` where resolution ∈
  {`coarse`=7×7=49, `medium`=14×14=196, `fine`=21×21=441}.
  ⚠️ There is **no `Test2D` class**; the 2D case-study model is
  `DoubleIntegratorApproxSim`. Boundary/goal/x0 are set inside the model class.
  ⚠️ `Main_ApproxSim.py --model` argparse only accepts `Dubins3DApproxSim` /
  `DoubleIntegratorApproxSim` (not `Test1D`); use `run_experiment.py` or
  `compare_methods.py` for 1D.

---

## 0. Four global principles (apply to every run)

1. **εmin must come from a fully-converged bisection** (tol = 1e-3) and the
   **complete probe trajectory** must be archived (every `mid`, its
   feasible/infeasible verdict, the final `hi`).
   ⚠️ Known incident: Test2D once returned εmin = 0.5. **Audit conclusion
   (2026-08-02)**: the bisection code (`epsilon_search.py:142-170`) is a standard
   correct bisection (`mid=(lo+hi)/2`, feasible→hi=mid else lo=mid, exit
   `hi-lo<=tol`); there is **no "first-probe-return" logic bug**. 0.5 is
   genuinely-OR-killed — it can be a legal converged value (if true εmin∈
   (0.499023,0.5], then ε=0.5 feasible, all probes <0.5 infeasible, 10 iters
   later hi stays 0.5, trajectory has ~11 entries), or a killed/incomplete run.
   **The only disambiguator is the probe trajectory**: a true-converged
   trajectory has ≥~10 `mid` entries with all <εmin probes infeasible; a killed
   trajectory has only ε=1/0/0.5 (two-three entries, never probes below 0.5).
   So the acceptance criterion is **trajectory fully converged**, NOT "εmin
   equals an early midpoint" — the true value *can* land on a midpoint
   (0.5, 0.25, …); do not reject on that basis.
2. **Every BCV run must record the tier breakdown**: how many sub-pairs each
   Tier (1 / 1.25–1.5 / 3) resolved, as a percentage. (Automatic via
   `tier_counts.json` from `run_experiment.py --method tiered`.)
3. **Timing**: run each (benchmark × semantics × method) combination **3 times**
   and take the mean (exceptions in §8); record node model, LP solver name &
   version, thread count. (Automatic via `env.txt`.)
4. **All results machine-readable on disk** (schema in §5); paper tables are
   generated from result files, never hand-copied.

---

## 1. E0: pre-flight checks (local, before any cluster task)

| # | task | acceptance |
|---|---|---|
| E0.1 | **Bisection mechanism check**: read `epsilon_search.py:142-170` (verified standard bisection, no logic bug); run one (15,5) competitive with verbose | Probe sequence complete (ε=1 → 0 → 0.5 → 0.25 → … until `hi-lo<=tol`, ~10 mids); do NOT look for a "first-probe-return" logic error — it doesn't exist |
| E0.2 | **Tier counter**: `check_coupling_tiered[_coop]` returns `decided_by` per sub-pair; `compute_approx_sim` now aggregates it into `tier_hist` and `compute_min_epsilon` exposes `tier_hist_final` (末次可行 probe). Wired through `_check_pair` → driver. | `run_experiment.py --method tiered` writes `tier_counts.json` non-empty |
| E0.3 | **Results-dumper**: `run_experiment.py` wraps `compute_min_epsilon`/`compute_approx_sim` and dumps the §5 schema (probe trajectory in `run.log`, `R_final.txt`, `tier_counts.json`, `result.csv`, `env.txt`) | smoke one run, all §3 files present & well-formed |

---

## 2. Experiment matrix

Priority: **P0** = cannot submit without it; **P1** = strongly recommended;
**P2** = optional/later.

### E1 (P0, top of queue): Test2D competitive full re-run

| field | content |
|---|---|
| model | 2D-DI (196,49) and 2D-DI (441,49) — i.e. `--fine medium/coarse` etc. |
| method | FCE (`--method corner`) + BCV (`--method tiered`), 3 reps each (see §8 for time-saving) |
| params | tol = 1e-3 |
| output | probe trajectory, εmin, \|R\|, wall time, LP calls, tier breakdown (BCV) |
| acceptance | ① probe trajectory **fully converged**: ≥~10 mids, `hi-lo<=tol`, all <εmin probes infeasible (whether it lands on an early midpoint is **irrelevant** — the true value can land on 0.5/0.25; do not reject on that; if true εmin ≈ 0.5 then accept it and revise the "ε consistently small" narrative); ② BCV ≡ FCE (εmin & R identical) |
| ref cost | old data: (441,49) FCE ≈ 13.3h, BCV ≈ 12.4h; (196,49) ≈ 1.5h |
| background | the old two rows εmin=0.5 are killed-run artifacts, \|R\|=441 un-sourced, **voided**; wall time & LP calls were real and retained |

### E2 (P0): Test1D (35,7) competitive archive re-run

| field | content |
|---|---|
| method | FCE + BCV full search, 3 reps each |
| extra output | ① final R full dump (verify \|R\| is 25 or 33); ② list of pairs pruned during fixed-point; ③ **tightest-sub-pair ranking** via `per_pair_epsilon.py` (each sub-pair's min feasible ε, top ranks; calls `compute_exact_g` per sub-pair); ④ label-consistency report (`mapping.py`, the seed 35→33 mismatch detail) |
| acceptance | ① εmin converges to 0.238281 ± tol with a complete probe trajectory; ② FCE is a *full* search (local曾 >15min timeout未完成, so the existing 0.238281 was obtained by tiered — **do NOT claim BCV≡FCE completeness for (35,7) until E2 cluster FCE lands**); ③ \|R\| is sourced (25 or 33 must have a run.log) |
| background | εmin=0.238 is real; the inflation mechanism is **boundary-label mismatch** (35/7 divides evenly but the boundary cells' goal/critical/normal labels disagree with the coarse parent), which the paper uses as a positive example |
| TBD | whether to also run a "label-aligned" (35,7) control (option: if the paper only tells the mismatch story, skip; if you want "after fix εmin drops to ~0.001" control data, run it) |

### E3 (P0): cooperative full data

| field | content |
|---|---|
| model | Test1D all 8 scales: (10,5)(15,5)(20,10)(21,7)(25,5)(35,7)(40,20)(51,17); Test2D two scales (**queue after E1 acceptance**) |
| method | FCE + BCV, 3 reps, tol = 1e-3 |
| acceptance | ① each scale BCV ≡ FCE; ② cooperative εmin ≤ competitive εmin (same scale) |
| already have | toy example (εmin=0.1, hand-verified) and 15→5 (εmin=0, \|R\|=15, trajectory PASS) verified locally — **no need to re-run the search**, but补 3-rep timing & tier breakdown then archive |
| note | 2D cooperative FCE uses a union-polytope response, LPs are larger, cost unknown — run (196,49) to probe before (441,49); **new scale (25,5) (5:1) smoke-test first** (`run_experiment.py --model 1D --fine 25 --coarse 5 --semantics cooperative --method corner --mode search`, confirm labels consistent, no error, εmin converges) before the long job |

### E4 (P0, lightweight): Test1D competitive BCV tier breakdown

| field | content |
|---|---|
| scope | 8 scales, only **BCV** re-run (FCE time/LP/εmin already real, archive as-is) |
| reps | 1 (just for tier counts; if machine differs from old data,补 3-rep timing) |

### E5 (P1): transitivity chain demo

| field | content |
|---|---|
| task | generate a new Test1D model pair **(40,10)** (4:1, a new ratio not covered by existing data; **smoke-test label consistency first**, then 3-rep timing), run competitive ε-search (FCE or BCV, 3-rep timing) |
| compare | existing ε_a of (40,20), ε_b of (20,10); check ε_direct(40→10) ≤ ε_a + ε_b |
| deliverable | three εmin + one conclusion (expected: direct is tighter, transitivity gives an upper bound — demonstrates Thm III.1) |

### E6 (P2, optional): reach-avoid end-to-end

| field | content |
|---|---|
| prerequisite | the engine supports interval value iteration (reach-avoid probability) — if not, do not write code |
| task | pick (35,7) or (51,17), define target/avoid via goal/critical labels, compute optimal policy satisfaction probability p̄(N) on the coarse model, output p̄ and p̄−δ_N over an N grid (δ_N = 1−(1−εmin)^N) |
| fallback | no numerical experiment; paper only plots the **analytic guarantee curve** δ_N(N) (one per benchmark, pure function, no run needed) |

### E7 (P1, key): fixed-tolerance single-shot verification — BCV's home-turf load

> **Motivation**: Table I's ε-search systematically concentrates probes near
> εmin's straddling region (the bracket crosses the threshold, BCV must
> degenerate to Tier 3 = FCE), so it measures BCV's **worst-case load**. BCV's
> home turf by design is "**one-shot verification at a given tolerance ε**"
> ("does this abstraction pass at ε=0.1?") — far from the boundary, Tier 1
> LP-free bulk-decides (loose ε → LBmin≥1−ε passes; tight ε → UB<1−ε rejects
> fast), and Tier 1 is **unconstrained by k₁≤K, always on**, so large k₁ (2D)
> may still benefit. Fixed-tolerance verification is more common in practice
> than min-ε. Corroboration: (35,7)'s 15.5× LP↓ happens precisely at
> εmin=0.238 (probes far from the boundary). This experiment tests whether BCV
> achieves an order-of-magnitude speedup under home-turf load.

| field | content |
|---|---|
| task | 4 benchmarks ((15,5),(35,7),(51,17),2D (441,49)) × fixed ε ∈ {εmin/2, 2εmin, 4εmin, 10εmin} as **single fixed-points** (no bisection), εmin = each one's Table I true value (2D uses E1's true value); BCV(tiered) vs FCE(corner), one each, record LP/wall |
| acceptance | far-from-boundary ε (e.g. 10εmin) should show a BCV LP↓ markedly larger than at εmin (Tier 1 bulk-decision); if 2D (441,49) also speeds up markedly at 10εmin → home-turf hypothesis holds, BCV story shifts from "mediocre constant speedup" to "order-of-magnitude under home-turf load, and predictably" |
| failure criterion | if 2D (k1=12) BCV≈FCE at all ε → Tier 1's O(2^{k1}) arithmetic (k1=12→4096 ops/sub-pair) already costs more than the LP it replaces, large-k1 home turf can't be saved either → BCV只剩 theory,走 Option B (pure sound LP-free lower bound) |
| cost | 4×4=16 single fixed-points, total machine time < one E1; parallelizable with E1 |
| paper landing | new §VII-C paragraph + optional Table: fixed-ε BCV vs FCE LP↓ vs ε/εmin; reframe §VII's BCV narrative from "constant speedup in εmin search" to "order-of-magnitude speedup under fixed-tolerance verification + εmin search degenerates to FCE" (echoes Remark 2) |

Command: `run_experiment.py --mode fixed --epsilon <value> --method {corner,tiered}`.

---

## 3. Files to archive per run

(produced automatically by `run_experiment.py`)

```
runs/<bench>_<nf>to<nc>__<sem>__<method>__<mode>__rep<i>/
├── run.log          # full bisection probe trajectory
├── result.csv       # one row, §5 schema
├── R_final.txt      # final relation (state-pair list)
├── tier_counts.json # BCV only: sub-pairs each tier resolved
└── env.txt          # node, CPU, solver name+version, threads, date, git commit
```

## 4. Acceptance checklist (tick before returning the data pack)

- [ ] probe trajectory complete, εmin converged (not an early-stop midpoint)
- [ ] BCV ≡ FCE (εmin, R identical; any discrepancy = implementation bug, report it, do not patch numbers)
- [ ] cooperative εmin ≤ competitive εmin (same scale)
- [ ] timing reps met, env.txt complete
- [ ] file naming & directory structure per §3

## 5. Results schema (results.csv, one row per run)

```
benchmark,n_fine,n_coarse,semantics,method,tol,rep,
epsilon_min,R_size,wall_time_s,lp_calls,
tier1_pct,tier125_15_pct,tier3_pct,
converged,probe_count,node,solver,commit
```

## 6. Paper-landing map

| paper location | data source | note |
|---|---|---|
| Table I (main) | E1/E2/E4 + existing competitive | per row: εmin, \|R\|, FCE/BCV time, Speedup, FCE/BCV LP, LP↓; 2D εmin/\|R\| only from E1 new data |
| Table II (tier breakdown) | E1/E3/E4 tier_counts | per row: Tier 1 / 1.25–1.5 / 3 resolve pct |
| Table III (semantics) | E3 vs existing/new competitive | per row: εmin(coop), εmin(comp), each wall time |
| Fig. scalability | all runs' wall_time vs n_fine | log axes, FCE/BCV two lines |
| Fig. reach-avoid / δ_N | E6 or pure analytic | — |
| text "εmin consistently small" | **do not write until E1 true value lands** | — |
| §VI-C / Remark 2 / conclusion "on both semantics" | **scope the claim until E3 lands** | — |
| conclusion "substantially reducing LPs" | Table I LP↓ column | 2D row may be an exception, scope the claim |
| (35,7) label-mismatch story | E2 label-consistency report + tightest-sub-pair ranking | — |
| transitivity "iterative abstraction refinement" | E5 | — |

## 7. Existing reusable data (no re-run, just archive)

- Test1D competitive (except (35,7)'s \|R\|): wall time, LP calls, εmin all real
  (recorded in `doc_en/running_example/scalable_test_record.md` etc.); ⚠️ that
  record is **lazy-vs-corner** (pre-`tiered` migration), competitive only; ε
  values transfer (sound+complete), LP/time are lazy-era.
- cooperative toy & 15→5 (补 timing & tier then archive);
- Test2D competitive: **only** wall time & LP calls (εmin/\|R\| voided, pending E1).

## 8. Suggested queue order & time-saving

1. **E0** (local, same day) — do not start any cluster task before E0.1 passes;
2. **E1** two 2D jobs first on the cluster (they dominate the timeline);
3. parallel: **E3** Test1D cooperative (mid-short) → **E2** → **E4**;
4. E3 2D cooperative queued after E1 acceptance (probe (196,49) cost before (441,49));
5. E5, E6 last.

**Time-saving**: 2D tasks whose goal is εmin/\|R\|/tier can run 1 rep; the 3-rep
timing requirement applies strictly only to ≤1h tasks. ⚠️ **timing-reuse caveat**:
the old 13h corresponded to the ε=0.5 (loose) run; if E1's true εmin is markedly
<0.5 (tighter ε → fixed-point harder, more LPs), the re-run will be **slower**,
and reusing 13h underestimates the speedup. If true εmin≈0.5 the timing is
comparable. Recommendation: re-measure 2D timing once on the converged run, or
note "wall time corresponds to the converged-εmin run".

---

## 9. Scope boundary (confirmed not done, 2026-08-02)

- **No test3D**: 1D/2D already close the narrative (1D=verify+tight ε+label
  mismatch story; 2D=stress test+Remark 2 limit). 3D corner count explodes, FCE
  likely infeasible, breaking the BCV≡FCE control design; and it exceeds the
  paper's "bounded corner sets" method positioning. If a reviewer asks about
  dimension, respond in one sentence in Discussion.
- **No new dynamics family**: the relation is binary, the variation axes =
  scale × coarse/fine ratio × semantics × algorithm, already enough. The only
  "third system" is E5's transitivity chain (40→20→10 vs direct 40→10), retained.
- **No 2D-map / car-trajectory visualization**: that is controller-synthesis
  evidence form; this paper's contribution is relation computation & error
  bounds. ε's practical meaning is shown by the δ_N analytic curve (zero cost)
  or E6 end-to-end numerical (if the engine already has interval value
  iteration); trajectory plots only as a spot if E6 completes and trajectory
  verification is already present, not developed specially.
