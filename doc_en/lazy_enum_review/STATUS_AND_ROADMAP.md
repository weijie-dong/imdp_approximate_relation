# Lazy Enumeration Review — Status & Roadmap

> Living document. Records the **current conclusions** of the theoretical
> review and the **step-by-step plan** to bring the lazy/enumeration machinery
> to formal-methods-grade rigor. Other docs in this folder hold the detail;
> this one is the index and tracker.
>
> Folder: `doc_en/lazy_enum_review/`
> - `lazy_enum_bugs_and_theory_review.md` — bug list + theory questions
> - `lazy_enum_soundness_analysis.md` — why the dual upper bound cannot certify feasibility
> - `lazy_enum_lower_bound_theory.md` — the sound lower-bound theory (derived + toy-validated)
> - `lazy_enum_fix_and_alternatives.md` — repair plan + alternatives
> - `STATUS_AND_ROADMAP.md` — **this file**

---

## 1. Context

- Algorithm 2 (`Competitive_Approximate_Relation_Computation.md`) computes the
  maximal competitive ε-approximate simulation relation via greatest-fixed-
  point iteration. The bottleneck is enumerating fine corners `C(x₁,a₁)`
  (≤ `2^(k1−1)`), one coupling LP per corner. Full enumeration is too slow at
  scale (e.g. 196→441 → 50h), which motivated the `method='lazy'` cutting-plane
  feature.
- This is a **formal-methods** result: the final `ε` and relation `R` must
  carry rigorous soundness/completeness guarantees.

## 2. Current conclusions

### 2.1 Defects found in the shipped lazy feature

1. **Bug A (confirmed)** — `_solve_separation_lp` (`lazy_enum.py:49–62`) uses
   `reversed(order)`, so it returns the corner that **maximizes** `pᵀα` (least
   likely to violate) instead of minimizing it. Verified by direct run.
2. **Bug B (minor)** — `lazy_enum.py:292` mislabels a final-iteration
   convergence break as `max_iter`.
3. **Bug C (doc)** — `lazy_enum_and_optimizations.md` §2.3/§8.6/§8.7 write
   `M(p) ≥ pᵀα*+τ*` (backwards; correct is `≤`) and over-claim
   "converged ⇒ sound (dual certificate)".

### 2.2 The fundamental soundness gap (not a patchable bug)

The lazy method's **True path** ("separation returned a checked corner ⇒ all
corners feasible") is **unsound and unrepairable by tweaking the dual**. The
coupling LP dual gives an **upper bound** `M(p) ≤ pᵀα+σ`; an upper bound
`≥ 1−ε` cannot certify `g := min_{c∈C} M(c) ≥ 1−ε`. Upper bounds certify
**infeasibility** only. This matches the project's own theory doc §3 (LP
duality cannot eliminate corner enumeration; Farkas dual-ray enumeration is
worst-case-equivalent to corner enumeration).

The **False path** (find a violating corner via primal LP) is sound and
salvageable (after Bug A fix).

### 2.3 New result: a sound lower-bound theory

Derived (see `lazy_enum_lower_bound_theory.md`):

- The coupling LP is a bipartite max-overlap problem with exact max-flow
  min-cut form: `Φ(p,q) = min_{A⊆U}[p(U\A)+q(N(A))]`.
- `g = min_c max_q min_A f(c,q,A)`, `f = c(U\A)+q(N(A))`.
- **Sound bracketing**: `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB`, where
  - `UB  = min_A[L₁(A)+U₂(N(A))]`        (upper bound; the "closed form" lazy mistook for exact)
  - `LB(q*) = min_A[L₁(A)+q*(N(A))]`      (sound lower bound for any fixed `q*∈P₂`)
  - `LB* = max_{q*} LB(q*)`                (tightest lower bound)
  - `LB_min = min_A[L₁(A)+L₂(N(A))]`      (parameter-free, weakest)
- The gap `UB − LB*` is the `min_c`/`max_q` **disjunction** (coarse response
  may depend on the fine corner). Gap = 0 ⇔ optimal coarse marginal is
  corner-independent ⇒ exact, **poly-time, LP-free** decision.
- All bounds are **submodular minimizations** ⇒ poly(k1), **no LP solves**.
- **Numerically validated** on 2 toy cases (bracket holds; gap observed as
  predicted).

### 2.4 Proposed sound-by-construction design

Tiered per-pair check (see `lazy_enum_fix_and_alternatives.md`):

```
Tier 1 (LP-free):  LB  vs 1−ε        → sound True (LB≥1−ε) or sound False (UB<1−ε)
Tier 2 (fast F):   lazy violator-search (Bug A fixed) → sound False
Tier 3 (exact):    full corner enumeration (Theorem V.3) → exact
```

**Key guarantee**: every tier is either a proven sound certificate or the exact
theorem; when uncertain it defers to the theorem. So the final `ε`/`R` are
**never less rigorous than the original Theorem V.3** corner enumeration. The
lower bound only ever adds sound shortcuts; it cannot weaken the guarantee
**as long as the Tier-3 fallback is retained**.

### 2.5 Honest rigor status

| Item | Status |
|---|---|
| Diagnosis (lazy unsound on True path) | **Rigorous** (standard LP duality + §3) |
| Max-flow min-cut form `Φ(p,q)` | **Rigorous** (classical) |
| Bracketing `LB ≤ g ≤ UB` | **✅ Proven** (Step 1, `formal_lower_bound_theorem.md` Thm 3) |
| Gap characterization (`UB−LB*` = minimax/saddle gap; =0 ⇔ universal coarse `q*`) | **✅ Proven** (Step 1, Prop 5) |
| Sound certificate (`LB≥1−ε ⟹ feasible`, `UB<1−ε ⟹ infeasible`) | **✅ Proven** (Step 1, Thm 4) |
| Closed forms `L₁,L₂,U₂` (general, nonzero lowers) | **✅ Proven** (Step 1, Lemma 2) — *corrects the informal zero-lower forms* |
| Submodularity of bound objectives | **❌ RETRACTED** (Step 1): `L₁` is supermodular; bounds are not submodular |
| Poly-time computability of bounds | **OPEN** (Step 1): exact & LP-free `O(2^{k₁}k₁)`; poly-time unknown |
| Real-benchmark validation | **Not done** (only 2 toy cases). → Step 2 |
| Implementation | **Not done** (design only). Current shipped code still unsound. → Step 4 |
| `corners.py` k1>12 unsound LP-fallback | **Still present** — separate soundness hole. → Step 6 |

**Bottom line (post-Step-1)**: the **soundness** keystone is rigorous — a sound
lower bound on `g` exists and is proven to certify feasibility; the bracketing
and gap characterization are theorems. The **speed** story is weaker than
initially hoped: bounds are exact and LP-free but **not** proven polynomial
(submodularity retracted). They remain a sound, LP-free pre-filter/certificate
with exact enumeration fallback — the formal guarantee on `ε`/`R` is intact.

### 2.6 Critical re-framing: ε is the *output*, not a free parameter  *(supersedes the (a)/(b) framing)*

`ε_min` is what the search *produces* — it measures the distance between the
two IMDPs. **Small ε = close systems = useful relation** (tight transfer bound);
**large ε ≈ 1 = systems far apart = meaningless** (`degradation = 1−(1−ε)^N →1`,
bound clamps to 0; the 5act→7act record confirms "bound holds but meaningless").
Two identical IMDPs ⇒ `ε_min = 0`.

This re-frames the two candidate methods:

- **(b) sound-but-incomplete (LB-only under-approximation) — RETRACTED.** It is
  effective only at *large* ε (where `1−ε` is small and `LB ≥ 1−ε` is easy), i.e.
  exactly the regime where the relation is meaningless. In the *useful* regime
  (small ε, `g` must approach 1) `LB` has a gap and (b) **collapses** — it drops
  the feasible pairs (the ones you want to keep), yielding `R'≈∅`. Step 2
  confirms: Test1D at `ε=0.001` certified only 15/75 feasible via `LB*`; at
  `ε=0.5` (large, easy) it certified 105/105. So (b) "works" only when the
  answer is worthless. **Do not use (b); do not write it into the paper.**

- **(a) tiered (bounds pre-filter + enumeration fallback) — VALID, sound + complete.**
  It is an *exact acceleration*, not a correctness compromise: same answer as
  Theorem V.3, faster where bounds decide. But it only speeds up the **easy
  parts**: the **infeasible side** (`UB<1−ε`, 0 enumeration — the ~40h of the
  50.8h case) and **large-ε binary-search iterations** (`LB` certifies feasible
  cheaply). It does **not** escape enumeration for the **tight-ε feasible core**
  — close systems at `ε≈ε_min` need `g→1`, `LB` has a gap, and sound
  certification requires full corner enumeration (the §3 barrier). Identical
  IMDPs (`ε=0`) are the worst case: every feasible pair must be exactly matched.

**Hard truth**: the useful regime (close systems, small ε) is exactly where
sound verification is most expensive and where the shipped `lazy` got its
speed *unsoundly* (shortcutting the tight-ε feasible pairs). There is **no
sound shortcut** for that core — consistent with §3 (corner enumeration cannot
be eliminated in the worst case). Honest paper positioning:
- Base Theorem V.3: sound+complete, exponential — **inherent** (§3).
- Bounds: sound *certificates* accelerating the easy parts; **not** a fast
  sound method for the close-relation regime.
- `lazy`: **not in the paper** (unsound).
- Practical levers for large cases: (a) pre-filter the infeasible side; (b)
  engineering (solver/parallelism/precompute); (c) **control `k1`** (coarser
  fine grid / fewer actions) to reduce `2^{k1}` at the source.

## 3. Open decisions (need user input before Tier-1 can be trusted without fallback)

- **D1**: When `LB ≥ 1−ε`, may we return `True` **without** the Tier-3
  fallback? The lower-bound theorem is now **proven** (Step 1), so this is
  *sound in principle*. Still recommended to keep the fallback until Step 2
  validates the bounds numerically on real benchmarks (a sign error in
  implementation could still betray the proof).
- **D2**: For `LB(q*)`, which `q*`? Candidate: the `μ₂` returned by one primal
  coupling LP on the initial hard corner (one LP/pair, then LP-free).
- **D3** *(revised after Step 1)*: Bound computation is **not** submodular-min.
  Choice is now: brute-force `2^{k₁}` (exact, LP-free, exponential) vs. an
  LP/combinatorial relaxation (open whether sound+poly). Decide per `k₁`
  regime after Step 2 measures residual sizes.

## 4. Step-by-step plan

Ordered. Each step has a deliverable and a "done when".

### Step 1 — Formalize the lower-bound theorem  *[theory, no code]* ✅ DONE
- Wrote `formal_lower_bound_theorem.md`: Lemma 1 (max-flow min-cut) ⇒
  Lemma 2 (extremal mass, general nonzero-lower forms) ⇒ Theorem 3
  (bracketing) ⇒ Theorem 4 (sound certificate) ⇒ Proposition 5 (gap =
  saddle/minimax gap).
- **Corrections found & recorded (§6)**: (i) lower-bound closed forms need
  nonzero lowers; (ii) submodularity/poly-time **retracted** — `L₁` is
  supermodular (counterexample given); bounds are exact+LP-free but poly-time
  is OPEN.
- *Done*: self-contained proof from standard tools (max-flow min-cut, weak
  minimax, box-simplex LP). Soundness rigorous; speed open.

### Step 2 — Validate bounds on real benchmarks  *[experiment, no code change to algorithm]* ✅ DONE
- Implemented `core/approx_sim/coupling_bounds.py` (LP-free `UB`/`LB_min`,
  LP-based `LB*`/exact `g`), unit-tested vs the running example.
- Driver `instrument_lower_bounds.py` (`--lbstar` tight breakdown,
  `--validate-g` bracket check vs exact `g`).
- Results (see `step2_large_scale_results.md`):
  - **Bracket validated on real Test1D**: 15→5 → 135/135 sub-pairs
    `LB_min ≤ LB* ≤ g ≤ UB` (0 fail); gap stats corroborate at 21→7, 35→7, 51→17.
  - **At ε=0.5 the bounds fully decide (0% residual) at every scale** —
    no enumeration needed.
  - **At tight ε≈0.001, residual shrinks with scale**: 44%→33%→28%→15%
    (15→5 … 51→17); the disjunction, needs enumeration.
  - Median gap ≈0 (most pairs exact); tail max 0.45→0.17, shrinking with scale.
  - k1 grows 4→9 (corners 32→512) across resolutions — the bottleneck the
    running example hides.

### Step 3 — Decide D1/D2/D3 from Step 2 data  *[decision]*
- Pick the `q*` strategy; set the `k1` threshold for brute-force vs solver;
- decide whether Tier-1 may stand alone (depends on Step 1 proof done).
- *Done when*: design frozen in this doc.

### Step 4 — Implement the tiered, sound `check_coupling`  *[code]*
- New module (e.g. `core/approx_sim/lazy_enum.py` rewrite or a new
  `coupling_tiered.py`) implementing Tier 1/2/3 with explicit `converged`/
  `fully_enumerated` flags.
- Fix Bug A (`reversed(order)`→`order`) and Bug B (explicit flag) in the
  violator-search.
- Wire submodular-min (brute force for small `k1`, solver for large).
- *Done when*: unit tests reproduce known `g` on toy cases; all-sound on a
  property test (never false-feasible vs ground truth).

### Step 5 — Rewrite docs to match the proven theory  *[docs]*
- Fix Bug C in `lazy_enum_and_optimizations.md` (§2.3/§8.6/§8.7): dual = upper
  bound = infeasibility certificate only; drop "exact/converged-sound" claims
  for the True path; describe the tiered sound design.
- Cross-link the formal proof (Step 1) and validation (Step 2).
- *Done when*: feature doc is consistent with §3 of the theory doc and with
  the formal proof.

### Step 6 — Address `corners.py` k1>12 fallback  *[code/docs]*
- Either make the high-d corner enumerator sound, or document it as
  "must not use; route to lower-bound/full-enum instead".
- *Done when*: no unsound corner-enumeration path can be reached by any
  `method=` flag.

### Step 7 — End-to-end correctness + performance  *[experiment]*
- Re-run `compare_methods.py`: tiered method vs `corner` baseline — identical
  `ε_min`/`|R|` (exactness), measure speedup and residual-enumeration fraction.
- Construct the regression case where the hardest corner is **not** the initial
  one and **not** pre-filterable (Test1D does not exercise this).
- *Done when*: exactness matches baseline on all benchmarks; speedup
  characterized; regression case passes.

## 5. Sequencing & dependencies

```
Step 1 (proof) ─┐
                ├─→ Step 3 (decide) → Step 4 (implement) → Step 7 (e2e)
Step 2 (validate)┘            ↑
        └─ also informs ──────┘
Step 5 (docs)  : after Step 1
Step 6 (corners): independent, can run in parallel with Steps 1–2
```

Steps 1 and 2 can run in parallel (theory + measurement). Nothing in the
codebase changes until Step 4. The shipped `method='lazy'` remains **unsound**
and must not be trusted for formal guarantees until Steps 1, 4, 7 complete.

## 6. Immediate next action

**Step 1 ✅ DONE** — soundness keystone proven (`formal_lower_bound_theorem.md`).
Two corrections recorded (nonzero-lower forms; submodularity/poly-time retracted).

**Step 2 ✅ DONE** — bounds validated on real Test1D
(`step2_large_scale_results.md`). Bracket holds (15→5: 135/135); at ε=0.5 the
bounds fully decide at every scale (0% residual); at tight ε the residual
shrinks with scale (44%→15%); median gap ≈0.

**Next: Step 3** (decide D1/D2/D3 from Step-2 data) → Step 4 (tiered sound
implementation). Key data point: at ε=0.5 no enumeration is ever needed, and
LB* (one LP/pair) certifies feasibility soundly — so the tiered design is
worth implementing. The shipped `method='lazy'` remains **unsound** until
Step 4.
