# Cooperative Semantics — Implementation Plan & Progress (Algorithm 1 FCE / Algorithm 3 BCV)

> Counterpart of `doc_zh/cooperative_implementation_plan.md` (English version for collaborators).
>
> Corresponds to paper `iMDP-apb.tex`: §V-B (Algorithm 1, cooperative FCE) and §VI (Algorithm 3,
> cooperative BCV). The engine `core/approx_sim/` previously implemented only the **competitive**
> semantics (Algorithm 2 / 4). This work adds the **cooperative** semantics.

---

## Implementation status: ✅ core complete, validated on toy + 1D (2026-08-01)

All of Steps 1–6 are coded and pass three-way agreement on the toy (paper Example 1 /
`new_running_example`), and the 1D Test1D benchmark is run locally.

| Step | Content | Status |
|---|---|---|
| 1 | Cooperative coupling primitive (collect V2_union + embed into common successor space) | ✅ `algorithm.py:_get_coarse_union` |
| 2 | Cooperative FCE driver (Algorithm 1, `semantics='cooperative'` branch) | ✅ `algorithm.py:_check_pair` |
| 3 | Cooperative BCV bounds (vertex enumeration, Lemma polytope-ext + LB*coop) | ✅ `coupling_bounds.py` (+4 functions) |
| 4 | Cooperative BCV driver (Algorithm 3) | ✅ `coupling_tiered.py:check_coupling_tiered_coop` |
| 5 | Wiring (argparse `--semantics` + add `tiered` to method choices + config/run_pipeline) | ✅ Main_ApproxSim / step2 / run_pipeline |
| 6 | Validation | ✅ see below |

### Toy validation (`run_cooperative_validation.py`, vs `design.md` §1.2 hand-calc)
- [1] cooperative ε_min = **0.1000** = hand ✓ (hard corner = β's (0,1))
- [2] Fixed-ε retain/remove of (p1,p2): all 6 ε match ✓
- [3] coop vs comp @ ε=0.1: both retain (p1,p2), |R|=3 ✓
- [4] **BCV == FCE** (completeness, Cor. `cor:completeness`): ε_min 0.1=0.1, retain/remove all match ✓
- [5] Per-sub-pair soundness: tiered decision vs `compute_exact_g_coop` ground truth, across
  ε={0.05,0.1,0.5}, **0 false-feasible / 0 false-infeasible**; tier distribution mirrors the
  competitive toy (β @ ε=0.05 infeasible via LP-free **ub_infeas** with 0 enumeration;
  ε=0.5 via **lbstar_feas**; tight-feasible via **enum_feas**) ✓

### 1D Test1D 15→5 (local, `compare_methods_cooperative.py`)

**Completeness (Cor. `cor:completeness`) holds at 1D scale:**

| | cooperative corner (FCE) | cooperative tiered (BCV) |
|---|---|---|
| ε_min | 0.000000 | 0.000000 |
| \|R_final\| | 15 | 15 |
| total LP | 1410 | 795 |
| wall | 6.17s | 5.61s |

Per-iteration trajectory MATCH (2 vs 2, 0 mismatches) → **[PASS] cooperative tiered == corner**.
tiered vs corner: 1.77× fewer LPs, 1.10× wall (ε_min=0 is an all-feasible easy regime; bounds
help little here).

**Cooperative vs competitive (semantic-difference empirical demo):**

| | cooperative (corner) | competitive (corner) |
|---|---|---|
| ε_min | **0.000000** | 0.000977 |
| \|R\| | 15 | 15 |
| wall | 6.17s | 43.29s |

- Cooperative achieves **exact simulation (ε=0)**; competitive needs ε≈0.001 →
  `eps_min(coop) ≤ eps_min(comp)` ✓ (randomized response enlarges the relation;
  cooperative relation ⊇ competitive relation — the 1D empirical demo of paper line 778).
- Cooperative is ~7× faster than competitive (no a2 loop, fewer sub-pairs).

### A bug fixed
`_get_coarse_union` initially held `_cache_lock` while calling `_get_corners`, which also locks
the same **non-reentrant** `threading.Lock` → the cooperative path deadlocked on first call.
The competitive path never hit the union cache, so it never surfaced. Fix: compute the union
**without** holding the lock (`_get_corners` is thread-safe on its own); only the final write
to `_union_cache` is guarded.

### Not yet done (follows competitive's cluster-handoff pattern)
2D 49→441 scale cooperative ε_min/timing. Code is ready — run on a cluster with
`--semantics cooperative --method {corner,tiered}` to fill the paper case-study table.
Competitive already ran the same three-way agreement on Test1D and 2D (see `design.md` §10–12).

---

## How to run (usage guide for collaborators)

The cooperative semantics is selected via the `--semantics` flag (default `competitive`).
Everything else (IMDP build, f2c mapping, ε binary search, fixed-point refinement) is shared
with the competitive path.

**End-to-end pipeline (single process):**
```bash
python Main_ApproxSim.py --model Test1D \
    --fine_resolution fine --coarse_resolution coarse \
    --semantics cooperative --method corner --lp_solver HIGHS
# or use the accelerated BCV:  --method tiered
# NOTE: Main_ApproxSim.py's --model argparse currently accepts only
#   Dubins3DApproxSim / DoubleIntegratorApproxSim (NOT Test1D). For 1D use
#   `run_experiment.py --model 1D --fine <n_cells> --semantics cooperative ...`
#   (the structured results-dumper, preferred) or `compare_methods_cooperative.py <nf> <nc>`.
#   2D: --model DoubleIntegratorApproxSim with --fine_resolution fine/medium/coarse.
```

**Pipeline via config / run_pipeline (build once, then pair):**
```bash
python run_pipeline.py build --config configs/approx_sim.yaml di_coarse_fine
python run_pipeline.py pair  --config configs/approx_sim.yaml di_coarse_fine --step 2
```
Add a `semantics: cooperative` key to the pair entry in `configs/approx_sim.yaml`
(see `run_pipeline.py` ~line 203 for forwarding).

**Step 2 standalone (from two IMDP pickles):**
```bash
python steps/step2_epsilon_search.py \
    --imdp_fine  output/<fine>/imdp.pkl \
    --imdp_coarse output/<coarse>/imdp.pkl \
    --output output/<pair>/eps.pkl \
    --semantics cooperative --method tiered --lp_solver HIGHS
```

**Validation scripts (deterministic, run in seconds–minutes):**
```bash
# toy: three-way agreement (FCE vs BCV vs hand), ε_min=0.1
python doc_en/new_running_example/run_cooperative_validation.py
# 1D Test1D 15->5: cooperative corner vs tiered (completeness) + competitive reference
python compare_methods_cooperative.py 15 5
```

Environment: `C:/Users/DWJ/.conda/envs/dyabstract/python.exe` (cvxpy/numpy/scipy).
`core.jax_config` (not `jaxconfig`).

**Direct API:**
```python
from core.approx_sim.epsilon_search import compute_min_epsilon
res = compute_min_epsilon(imdp1, imdp2, f2c_map, part1, part2,
                          method='tiered',          # or 'corner'
                          semantics='cooperative',   # <-- select cooperative
                          lp_solver='HIGHS', tol=1e-3)
# res['epsilon_min'], res['R_final']
```

---

## 0. Key correction: cooperative ≠ "∀a1 ∃a2 pick a defender coarse action"

An initial code survey mis-described cooperative as the competitive loop with inner/outer swapped
(∀a1 ∃a2, find a coarse action as defender). **This contradicts the paper; implement per the paper.**

The paper (Def `def:Coupling Constraint for Corners` line 1317, Thm `thm:IMDP-coupling-constraint`
item (i), §VI line 1790) is explicit: the cooperative coarse response is a **randomized mixture over
ALL coarse actions** ρ ∈ Dis(Γ2(x2)), reduced to a single convex combination with vertex set

```
V2 = ⋃_{a2∈Γ2(x2)} C(x2,a2)        # union of all per-action corners
Q  = conv(⋃_{a2} P2(x2,a2))         # response polytope
```

So the cooperative driver has **no a2 loop**:

```
competitive (already implemented, algorithm.py:179-288):
    for a2 in Γ2(x2):              # ∀a2
        for a1 in Γ1(x1):         #   ∃a1 (find a defender)
            for c1 in C(x1,a1): check_coupling(c1, V2=C(x2,a2))   # ∀c1
            if all feasible: found; break
        if not found: remove (x1,x2)

cooperative (Algorithm 1):
    for a1 in Γ1(x1):              # ∀a1
        V2_union = ⋃_{a2} C(x2,a2)
        for c1 in C(x1,a1):        #   ∀c1
            if not check_coupling(c1, V2=V2_union) feasible: remove (x1,x2); break
```

**Good news:** `coupling.py:check_coupling(c1, V2, succ1_ids, succ2_ids, R_local, epsilon)` is
already structured as "fine side = fixed corner c1 (∀), coarse side = β-mixture over V2 (∃)" —
exactly the cooperative role split (fine side = the simulated system M1 is the ∀ adversary;
coarse side = M2 is the ∃ responder). So **cooperative FCE reuses `check_coupling` as-is**,
only with V2 = "union of all coarse-action corners". Competitive also reuses it, just with
V2 = single-action corners. **No mirrored formulation needed.**

> ⚠️ The existing toy script `doc_en/running_example/validate_lower_bound_running_example.py:217-227`
> computes cooperative as "pure a2 selection" (`max over a2 of g(a1,a2)`) by brute force. That is
> **not** the paper's randomized response — pure-action selection is an under-approximation and yields
> a smaller relation than the union form (paper line 778: randomization is "strictly necessary" and
> enlarges the relation). After the engine version landed it should be reconciled/replaced.

## 1. Algorithm difference cheat-sheet

| Dimension | Competitive (implemented) | Cooperative (now implemented) |
|---|---|---|
| Response polytope Q | `P2(x2,a2)` single-action box–simplex | `conv(⋃_{a2} P2(x2,a2))` all-action union |
| Vertex set V_Q | `C(x2,a2)` single-action corners | `⋃_{a2} C(x2,a2)` union (superset, sound) |
| FCE driver inner loop | for a2, for a1, for c1 (find found) | for a1, for c1 (any infeasible → remove; no a2 loop) |
| Coupling LP's V2 | `C(x2,a2)` | `⋃_{a2} C(x2,a2)` |
| BCV extremal mass U2/L2 | box–simplex closed form (Lemma `lem:boxsimplex`) | polytope vertex enumeration (Lemma `lem:polytope-ext`) |
| Other BCV-Check tiers | same (semantics-agnostic) | same |
| g_Q definition | `min_{c∈C(P1)} max_{q∈Q} Φ(c,q)` | same (only Q differs) |

## 2. Core implementation challenge: cross-action common successor space

Cooperative V2 is the **union of corners across all a2**. Different a2 may have different successor
sets `succ2(a2)`. `check_coupling` requires every V2 corner to be a length-k2 vector with
`len(succ2_ids) == k2`. So each action's corners must be **embedded into a common successor space**:

```
succ2_union = dedup(⋃_{a2∈Γ2(x2)} succ2(a2))      # common coarse successor IDs
for each a2, each c2 ∈ C(x2,a2):
    v_embed = zeros(|succ2_union|)
    for the t-th successor sid of succ2(a2):
        v_embed[ index(sid in succ2_union) ] = c2[t]
    V2_union.append(v_embed)
```

Thus V2_mat is [L × |succ2_union|], W is [k1 × |succ2_union|], fully compatible with `check_coupling`.
R_local (s1,s2) matching uses real state IDs and is unaffected by the embedding.

## 3. Step-by-step implementation (file/function anchors)

### Step 1 — Cooperative coupling primitive  `corners.py` / `coupling.py`
- `_get_coarse_union(s2)` in `algorithm.py`: collects `succ2_union` (de-duplicated, order-preserving)
  + `V2_union` (embedded corner list). Reuses `enumerate_corners` / `_get_corners`
  (per-(x2,a2) corners are cached).

### Step 2 — Cooperative FCE driver (Algorithm 1)  `algorithm.py`
- `cooperative` branch in `_check_pair`:
  ```
  for a1 in range(num_a1):
      corners1, succ1, pl1, pu1 = _get_corners(1, s1, a1)
      # fine pre-filter (reuse fine_has_r, but succ2_set = succ2_union_set)
      for c1 in corners1:
          if not check_coupling(c1, V2_union, succ1, succ2_union, R_frozen, epsilon, ...):
              return ((s1,s2), ...)        # any infeasible → remove pair
  ```
- No a2 loop, no found_defender.
- `compute_approx_sim` gained a `semantics='competitive'` parameter dispatching to the branch.
- Pre-filter `succ2_set` uses the union (coarse response can land on any a2's successors).

### Step 3 — Cooperative BCV bounds  `coupling_bounds.py`
Existing `compute_bounds_lpfree(pl1,pu1,succ1,pl2,pu2,succ2,R)` treats the coarse side as a
box–simplex (closed-form U2/L2). Cooperative Q = conv(⋃ P2(x2,a2)) is **not** a box–simplex; use
**polytope vertex enumeration** (Lemma `lem:polytope-ext`):
`min_{q∈Q} q(S) = min_{v∈V_Q} v(S)`, `max = max_{v∈V_Q} v(S)`, V_Q = ⋃ C(x2,a2) (superset, sound).

Added:
- `compute_bounds_lpfree_coop(pl1,pu1,succ1, V_Q_mat, succ2_union, R)`: subset enumeration A⊆U
  unchanged (fine side), but U2/L2 enumerate V_Q vertices for extremes.
- `compute_lb_star_coop(...)`: q* ∈ conv(V_Q) constraint (`q* = β @ V_Q_mat, β≥0, Σβ=1`) instead
  of the box constraint.
- `_vertex_mass_min/_max`, `compute_exact_g_coop` (validation reference).

### Step 4 — Cooperative BCV driver (Algorithm 3)  `coupling_tiered.py`
- `check_coupling_tiered_coop(...)`: Tier1 (LP-free coop bounds) → Tier1.25 (hardest-corner probe
  LP, V2=union) → Tier1.5 (LB* coop) → Tier3 (per-corner `check_coupling(c1, V2_union)`, == FCE).
- Reached via `semantics='cooperative'` + `method='tiered'`.

### Step 5 — Wiring
Threaded `semantics` + `method` through:
- `epsilon_search.compute_min_epsilon`
- `steps/step2_epsilon_search.py` (`--method` choices, ~line 49)
- `Main_ApproxSim.py` (argparse choices, ~line 108)
- `run_pipeline.py` / `configs/approx_sim.yaml`

**Also fixed a pre-existing issue:** `Main_ApproxSim` and `step2` argparse `choices` both omitted
`tiered`; added.

### Step 6 — Validation
1. **Completeness** (Corollary `cor:completeness`): on the same benchmark, cooperative FCE == BCV
   (relation R and ε_min byte-identical). ✅ on toy and 1D.
2. **Timing**: cooperative FCE vs BCV on small benchmarks; verify speedup. ✅ on 1D.
3. **vs competitive**: cooperative (no a2 loop + randomized enlarges relation) should be faster
   with ε_min ≤ the competitive value. ✅ on 1D (ε=0 vs 0.000977, ~7× faster).

## 4. Decision record
- Code organization: **in-place branches in existing files** (cooperative branches inside
  algorithm.py / coupling_bounds.py / coupling_tiered.py, dispatched by the `semantics` param).
  Maximizes reuse, sits side-by-side with competitive for easy comparison.
- Phasing: **FCE first, then BCV**. Steps 1+2 landed cooperative FCE and reconciled with the toy
  before Steps 3+4 (BCV). Staged validation, lower risk.

## 5. Key file pointers
- `core/approx_sim/algorithm.py:30` `compute_approx_sim` (dispatcher); `:162` `_check_pair`
  (competitive ∀a2∃a1 at :179-288; cooperative branch + `_get_coarse_union` above it)
- `core/approx_sim/coupling.py:16` `check_coupling` (reused); `:197` `check_coupling_max_mass`
- `core/approx_sim/corners.py:44` `enumerate_corners`; `:24` `get_successor_info`
- `core/approx_sim/coupling_bounds.py:87` `compute_bounds_lpfree`; `:172` `compute_lb_star`;
  `:142` `compute_exact_g`; + `_vertex_mass_min/max`, `compute_bounds_lpfree_coop`,
  `compute_lb_star_coop`, `compute_exact_g_coop`
- `core/approx_sim/coupling_tiered.py:115` `check_coupling_tiered`; `check_coupling_tiered_coop`
- `core/approx_sim/epsilon_search.py` `compute_min_epsilon` (forwards `semantics`)
- `steps/step2_epsilon_search.py` `--semantics` / `--method` choices; `Main_ApproxSim.py` ditto
- `run_pipeline.py` (~line 203) forwards config `semantics` key
- Validation: `doc_en/new_running_example/run_cooperative_validation.py` (toy);
  `compare_methods_cooperative.py` (1D Test1D 15→5)
- toy reference (pure-a2 brute force, under-approx): `doc_en/running_example/validate_lower_bound_running_example.py:217-227`;
  semantics notes + ε_min records: `doc_en/new_running_example/design.md:33-48`
