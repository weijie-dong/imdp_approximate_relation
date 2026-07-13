> **⚠️ SUPERSEDED by `formal_lower_bound_theorem.md` (Step 1).** Writing the
> formal proof exposed two errors in this informal doc:
> 1. The closed forms `L₁(A)=max(0,1−Σ_Aû_i)` and `L₂(S)=max(0,1−Σ_{∉S}û²_j)`
>    are the **zero-lower-bound special case**. General IMDPs have nonzero
>    lowers; correct forms are in Lemma 2 of the formal doc.
> 2. The **submodularity / polynomial-time claim is retracted.** `L₁` is
>    supermodular (counterexample in formal doc §6), so the bounds are **not**
>    submodular and submodular-minimization does **not** apply. Bounds remain
>    **sound, exact, and LP-free** (`O(2^{k₁}k₁)`), but **poly-time is OPEN**.
>
> **Soundness (the formal-methods-critical part) is unaffected and now formally
> proven.** The informal text below is kept for intuition only; treat the
> formal doc as authoritative.

# A Sound Lower-Bound Theory for the Coupling Feasibility Check

> Answers the request: *derive a precise lower bound for `g = min_{c∈C} M(c)`*,
> where `M(c)` is the max in-relation coupling mass for fine corner `c`. The
> lazy method's soundness bug stems from using an **upper** bound (the LP dual)
> to certify feasibility, which is impossible. This document derives a genuine
> **lower** bound that *can* certify feasibility, characterizes exactly when it
> is tight, and is **numerically validated**.
>
> Companion to `lazy_enum_soundness_analysis.md` (which proves the upper bound
> cannot certify feasibility) and `lazy_enum_bugs_and_theory_review.md`.

---

## 1. Why a lower bound is the right object

The pair `(x₁,x₂,a₁,a₂)` is feasible ⟺ `g := min_{c∈C} M(c) ≥ 1−ε`. To declare
**feasible (sound `True`)** we need a **lower bound on `g`** that is `≥ 1−ε`.
The LP dual gives an **upper** bound (`M(p) ≤ pᵀα+σ`), which can certify
**infeasibility** (`UB < 1−ε ⇒ g < 1−ε`) but never feasibility. This is the
gap §3 of `Competitive_Approximate_Relation_Computation.md` identifies and the
lazy doc §2.3 gets backwards. We need a lower bound. Below is one.

---

## 2. Structure: the coupling LP is a max-overlap / transportation problem

The coupling maximizes `W(R)` (mass on relation pairs) with fine marginal `p`
(fixed = corner `c`) and coarse marginal `q` free in `P₂`:

```
M(p) = max_{q∈P₂}  max_{W: marg(p,q)}  W(R).
```

Key fact: for **fixed** `p, q`, `max_{W} W(R)` is a bipartite max-flow and has
an exact min-cut closed form. Network: `s→u_i` (cap `p_i`), `u_i→v_j` (cap `∞`
iff `(i,j)∈R`), `v_j→t` (cap `q_j`). Max-flow = max mass routable through `R`.
Min-cut (source side = `{s}∪A∪B`, `A⊆U`, `B⊇N(A)` to avoid cutting an `∞` edge,
`N(A)={j:∃i∈A,(i,j)∈R}`):

```
Φ(p,q) := max_W W(R) = min_{A⊆U} [ p(U\A) + q(N(A)) ].     (exact)
```

Hence

```
M(p) = max_{q∈P₂}  min_{A⊆U} [ p(U\A) + q(N(A)) ],
g     = min_{c∈C}  M(c)  =  min_{c∈C}  max_{q∈P₂}  min_{A⊆U} f(c,q,A),
```

with `f(c,q,A) = c(U\A) + q(N(A))`, **bilinear** in `(c,q)` for each `A`.

---

## 3. The disjunction (why a closed form is only an *upper* bound)

Swapping `min_c` / `max_q` is **not** free. By weak minimax duality only:

```
g = min_c max_q min_A f  ≤  min_A [ (min_c c(U\A)) + (max_q q(N(A))) ].
```

Define the per-polytope extremal mass functions (`û,û²` = upper bounds,
`l²` = coarse lower bound; `S⊆U` or `⊆V`):

```
L₁(A) := min_{c∈C} c(U\A) = max(0, 1 − Σ_{i∈A} û_i)         (min fine mass outside A)
U₂(S) := max_{q∈P₂} q(S)   = min(Σ_{j∈S} û²_j, 1 − Σ_{j∉S} l²_j)  (max coarse mass on S)
```

Then the **upper bound**

```
UB := min_{A⊆U} [ L₁(A) + U₂(N(A)) ]   ≥   g.                (sound upper bound)
```

`UB` is the "closed form" one might naively hope equals `g`. It does **not** in
general — the gap is the `min_c`/`max_q` swap, i.e. exactly the disjunction
§3.3 describes (the coarse response `q` may depend on the fine corner `c`;
forcing a single `q` for all `c` loses tightness). This is the same barrier that
makes the lazy dual certificate fail.

---

## 4. The lower bound (the new, sound object)

We now bound `g` from **below**. Use `max_q ≥` any fixed `q*`, and
`min_c min_A = min_A min_c`:

```
g  =  min_c max_q min_A f   ≥   max_{q*∈P₂}  min_c min_A f(c,q*,A)
   =: max_{q*∈P₂}  LB(q*),     where
LB(q*) := min_{A⊆U} [ L₁(A) + q*(N(A)) ].
```

So **for every fixed `q*∈P₂`, `LB(q*) ≤ g`** is a sound lower bound. The
tightest is `LB* := max_{q*∈P₂} LB(q*) ≤ g`. Dropping the `q`-choice entirely
gives the weakest but parameter-free bound (use `max_q ≥ min_q`):

```
LB_min := min_{A⊆U} [ L₁(A) + L₂(N(A)) ]   ≤   g,
L₂(S) := min_{q∈P₂} q(S) = max(0, 1 − Σ_{j∉S} û²_j).        (min coarse mass on S)
```

### Bracketing theorem (validated)

```
LB_min  ≤  LB(q*)  ≤  LB*  ≤  g  ≤  UB.
```

- All four bounds are **sound** (LB's ≤ g ≤ UB).
- The gap `UB − LB*` is precisely the `min_c`/`max_q` disjunction. It is **0**
  iff the optimal coarse marginal is corner-independent (same `q*` is worst for
  every fine corner) — then `LB* = g = UB` and the pair is decidable exactly
  without enumerating corners.
- When the gap is **nonzero**, no cheaper-than-enumeration method can decide
  feasibility in the worst case (consistent with §3); the bounds may straddle
  `1−ε` and leave the pair inconclusive.

### Numerical validation

`U=V={0,1,2}`, `R={(0,0),(0,1),(1,1),(2,2)}`, fine `û=[0.7,0.5,0.6]`,
coarse `û²=[0.8,0.9,0.7]`, lowers all 0. Brute-force `g` vs bounds:

```
g      = 0.80
LB_min = 0.20      LB* = 0.50      UB = 1.00
        LB_min ≤ LB* ≤ g ≤ UB   ✓
        gap UB − LB* = 0.50   (the disjunction, nonzero as expected)
```

---

## 5. Polynomial computability (submodular minimization)

Each bound is a minimum over subsets `A⊆U` of a **submodular** set function:

- `L₁(A)=max(0,1−Σ_{i∈A}û_i)` — positive part of a modular function ⇒ submodular.
- `q*(N(A))` and `L₂(N(A))`, `U₂(N(A))` — `N(·)` is a union/neighborhood map
  (`N(A∪B)=N(A)∪N(B)`) and `q*(·)`, `L₂(·)`, `U₂(·)` are submodular increasing
  in their set argument; composing a submodular-increasing function with the
  union-neighborhood preserves submodularity.
- Sums of submodular functions are submodular.

**Unconstrained submodular minimization is polynomial in `|U|=k1`** (Orlin et
al., independent of `2^k1`). Hence:

- `LB_min`, `LB(q*)`, `UB` are computable in **poly(k1)** time — and involve
  **no LP solves** (unlike corner enumeration, which solves one LP per corner).
- `LB* = max_{q*∈P₂} LB(q*)` maximizes a concave (min-of-affine) function over
  `P₂`; exact maximization is the hard half (exponential in the worst case,
  consistent with §3), but **any feasible `q*` already gives a sound lower
  bound** — we never need the exact max to obtain a certificate.

Practical `q*` choices (cheap, sound): reuse the `μ₂` the primal coupling LP
returned for the initial hard corner; or try each coarse corner; or use
`LB_min` which needs no `q*` at all.

---

## 6. Sound feasibility certificate (this is what lazy was missing)

```
Compute LB  (e.g. LB_min, or LB(q*) with q* = a primal μ₂).

  if LB ≥ 1 − ε :  return FEASIBLE        (sound True  — lower bound certifies g ≥ 1−ε)
  if UB < 1 − ε :  return INFEASIBLE      (sound False — upper bound certifies g < 1−ε)
  else           :  INCONCLUSIVE          (bounds straddle 1−ε; must enumerate / fallback)
```

Both decisions are **exact/sound**; only the straddling case needs work. This
replaces the lazy method's unsound `converged ⇒ True`.

Note the symmetry with the lazy violator-search: the lazy LP-dual path is
another way to produce **upper bounds** (sound `False`); this lower-bound path
produces **sound `True`**. They are complementary, not redundant.

---

## 7. Relation to §3 (no contradiction)

§3 says corner enumeration cannot be eliminated **in the worst case**. This
result does **not** refute that:

- When the disjunction gap is nonzero and the bounds straddle `1−ε`, deciding
  still requires enumeration (worst case unchanged).
- The novelty is that (a) there is **always** a poly-time sound lower bound,
  (b) there is a **characterized subclass** (corner-independent coarse
  response, gap=0) decidable exactly in poly time with **no LPs**, and
  (c) even when not exact, the bounds often clear `1−ε` from one side,
  resolving the pair without enumeration.

So the lower bound does not break the §3 barrier; it carves out a practically
large region where the barrier does not bite, and otherwise narrows the
residual that must be enumerated.

---

## 8. Limitations & open points

1. **Gap can be large** (validation shows `0.5`). Tightness requires
   corner-independent optimal `q`. How common is this on real benchmarks
   (Test1D, DoubleIntegrator, Dubins)? Needs experiments.
2. **Submodular-min in practice**: poly in theory, but generic solvers are
   heavy. For small `k1` (≤ ~16) brute-force over `2^k1` subsets is fine and
   still **LP-free** (the LP was the 95% cost). A fast specialized solver
   (e.g. for this `L₁ + coverage` form) may exist — open.
3. **`LB*` exact maximization** is exponential; we rely on heuristic `q*`. How
   to pick `q*` to maximize the chance of `LB ≥ 1−ε`? Candidate: solve the
   primal coupling LP once on the **initial hard corner**, take its `μ₂` as
   `q*`. (Open: prove or test.)
4. The bounds are **per `(s₁,a₁,s₂,a₂)`**; they do not remove the outer loops
   over pairs/actions (those are not the bottleneck).

---

## 9. Bottom line

- A sound, poly-time, **LP-free lower bound** on `g` exists
  (`LB_min`, and the tighter `LB(q*)`).
- It certifies **feasibility** (`g ≥ 1−ε`) whenever it clears the threshold —
  exactly the certificate the lazy method lacks.
- It is **not always exact** (gap = the §3 disjunction), so it is a *partial*
  exact method: exact on a characterized subclass, sound-but-conservative
  otherwise, with a clean fallback to enumeration when the bounds straddle.
- This is a real fix path for the lazy soundness bug, and a candidate
  alternative when full enumeration is too slow. See
  `lazy_enum_fix_and_alternatives.md` for the concrete plan.
