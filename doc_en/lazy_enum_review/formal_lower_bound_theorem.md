# Formal Theorem & Proof: Sound Bounds for the Coupling Feasibility Check

> Step 1 deliverable (keystone). Self-contained, peer-review-grade derivation of
> the sound lower/upper bounds on `g = min_{c∈C} M(c)`. Read alongside
> `lazy_enum_lower_bound_theory.md` (informal version) and
> `lazy_enum_soundness_analysis.md`.
>
> **Two corrections vs. the informal doc are recorded in §6.** The most
> important: the *submodularity / polynomial-time* claim does **not** hold as
> stated. The **soundness** results (the part that matters for formal methods)
> are rigorous and unaffected.

---

## 0. Notation and standing assumptions

Fix a pair `(x₁,x₂)∈R`, fine action `a₁`, coarse action `a₂` (the per-pair
context of Algorithm 2, Theorem V.3). Let

- `U = {1,…,k₁}` fine successors; `V = {1,…,k₂}` coarse successors.
- Fine interval polytope
  `P₁ = {p∈ℝ^{k₁}_{≥0} : Σ_i p_i = 1, l̂_i ≤ p_i ≤ û_i}` (assume nonempty:
  `Σl̂ ≤ 1 ≤ Σû`). `C := vert(P₁)` (≤ `2^{k₁−1}` vertices).
- Coarse interval polytope
  `P₂ = {q∈ℝ^{k₂}_{≥0} : Σ_j q_j = 1, l²_j ≤ q_j ≤ û²_j}`.
- `R ⊆ U×V`: successor pairs in the current relation.
- Neighborhood: `N(A) := {j∈V : ∃i∈A, (i,j)∈R}` for `A⊆U`.
- For a distribution `r` and set `S`, `r(S) := Σ_{i∈S} r_i`.

**Coupling value.** For fine marginal `p∈P₁` and coarse marginal `q∈P₂` define

```
Φ(p,q) := max{ W(R) : W∈ℝ^{U×V}_{≥0},  Σ_j W_{ij}=p_i ∀i,  Σ_i W_{ij}=q_j ∀j },
```

where `W(R)=Σ_{(i,j)∈R}W_{ij}`. (This is the max in-relation coupling mass; the
coarse marginal is free in `P₂` because Definition 5 lets `μ₂=Σβ·c²` range over
`conv(vert(P₂))=P₂`.)

**Per-corner and global quantities:**

```
M(c) := max_{q∈P₂} Φ(c,q)        (best coarse response to corner c)
g     := min_{c∈C} M(c).          (hardest corner)
```

By Theorem V.3 (corner reduction), the pair `(x₁,x₂,a₁,a₂)` is **ε-feasible**
**iff** `g ≥ 1−ε`. Certifying feasibility thus requires a **lower bound on g**.

---

## 1. Lemma (max-flow / min-cut form of Φ)

*For any `p∈P₁, q∈P₂`:*

```
Φ(p,q) = min_{A⊆U} [ p(U\A) + q(N(A)) ].
```

**Proof.** `Φ(p,q)` is the value of a bipartite max-flow: source `s`, sink `t`;
edges `s→i` of capacity `p_i`; edges `i→j` of capacity `∞` iff `(i,j)∈R`
(else absent); edges `j→t` of capacity `q_j`. A feasible `s–t` flow is exactly a
matrix `W≥0` with row sums `p_i` and column sums `≤q_j`; because `Σp=Σq=1`, an
optimal flow saturates all `j→t` and yields row sums `p`, column sums `q`.
Hence max-flow value `= Φ(p,q)`.

By the max-flow/min-cut theorem this equals the min `s–t` cut. A finite cut
places some `A⊆U` and `B⊆V` on the source side; to avoid cutting an `∞`-edge
`i→j` (`i∈A`, `j∉B`), it must be that `N(A)⊆B`. Given `A`, the cheapest such
`B` is `B=N(A)` (capacities `q_j≥0`). The cut value is then
`Σ_{i∉A}p_i + Σ_{j∈N(A)}q_j = p(U\A)+q(N(A))`. Minimizing over `A⊆U` gives the
claim. ∎

Define `f(p,q,A) := p(U\A)+q(N(A))`, so `Φ(p,q)=min_{A⊆U}f(p,q,A)`, and

```
M(c) = max_{q∈P₂} min_{A⊆U} f(c,q,A),     g = min_{c∈C} max_{q∈P₂} min_{A⊆U} f(c,q,A).
```

---

## 2. Lemma (extremal mass on a box-simplex)

*Let `P={x∈ℝⁿ_{≥0}:Σx=1, l≤x≤û}` be nonempty and `S⊆[n]`. Then*

```
min_{x∈P} x(S) = max( Σ_{i∈S} l_i , 1 − Σ_{i∉S} û_i ),
max_{x∈P} x(S) = min( Σ_{i∈S} û_i , 1 − Σ_{i∉S} l_i ).
```

**Proof (sketch, both bounds are tight constructions).** For the minimum: each
`x_i≥l_i` gives `x(S)≥Σ_{i∈S}l_i`; and `x(S)=1−x([n]\S)≥1−Σ_{i∉S}û_i`. Hence
`x(S)≥max(Σ_S l, 1−Σ_{∉S}û)`. The bound is attained: if `Σ_S l ≥ 1−Σ_{∉S}û`,
set `x_i=l_i` on `S` and distribute `1−Σ_S l` over `[n]\S` (feasible by the
case condition and `Σl≤1`); if `Σ_S l < 1−Σ_{∉S}û`, set `x_i=û_i` on
`[n]\S` and `x(S)=1−Σ_{∉S}û` on `S` (feasible by `Σû≥1`). The maximum is dual
(replace `l↔û`, `S↔[n]\S`). ∎

Apply with `P=P₁` (minimum is attained at a vertex since `x(S)` is linear):
`L₁(A) := min_{c∈C}c(U\A) = max(Σ_{i∈U\A}l̂_i, 1−Σ_{i∈A}û_i)`.
Apply with `P=P₂` for `S⊆V`:
`U₂(S) := max_{q∈P₂}q(S) = min(Σ_{j∈S}û²_j, 1−Σ_{j∉S}l²_j)`,
`L₂(S) := min_{q∈P₂}q(S) = max(Σ_{j∈S}l²_j, 1−Σ_{j∉S}û²_j)`.

*(If all lower bounds are 0, these reduce to `L₁(A)=max(0,1−Σ_{i∈A}û_i)`,
`U₂(S)=min(Σ_{j∈S}û²_j,1)`, `L₂(S)=max(0,1−Σ_{j∉S}û²_j)` — the forms used in
the informal doc.)*

---

## 3. Theorem (Sound bracketing of g)

*Define*

```
UB      := min_{A⊆U}[ L₁(A) + U₂(N(A)) ]              (upper bound)
LB(q*)  := min_{A⊆U}[ L₁(A) + q*(N(A)) ]  (q*∈P₂)     (lower bound, any fixed q*)
LB*     := max_{q*∈P₂} LB(q*)                          (tightest lower bound)
LB_min  := min_{A⊆U}[ L₁(A) + L₂(N(A)) ]              (parameter-free lower bound)
```

*Then* `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB`. *In particular `LB_min, LB(q*), LB*`
are sound lower bounds on `g`, and `UB` is a sound upper bound.*

**Proof.** All inequalities use only weak minimax (the universal fact
`sup_y inf_x F ≤ inf_x sup_y F`, i.e. `max≤min-max`) and that `min`'s commute.

*Upper bound.* For fixed `c`, `M(c)=max_q min_A f(c,q,A) ≤ min_A max_q f(c,q,A)`
(weak minimax). Now `max_{q∈P₂}f(c,q,A)=c(U\A)+max_{q∈P₂}q(N(A))=c(U\A)+U₂(N(A))`,
independent of `q` after maximizing. Hence

```
g = min_c M(c) ≤ min_c min_A[ c(U\A)+U₂(N(A)) ]
              = min_A[ (min_c c(U\A)) + U₂(N(A)) ]      (min_c, min_A commute)
              = min_A[ L₁(A)+U₂(N(A)) ] = UB.
```

*Lower bound.* For fixed `c` and any fixed `q*∈P₂`,
`M(c)=max_q min_A f ≥ min_A f(c,q*,A)` (`max ≥ any value`). Thus

```
g = min_c M(c) ≥ min_c min_A[ c(U\A)+q*(N(A)) ]
              = min_A[ L₁(A)+q*(N(A)) ] = LB(q*).
```

Taking `max_{q*}` keeps the inequality: `g ≥ LB*`. Finally
`LB* = max_q LB(q) ≥ min_q LB(q) = min_q min_A[L₁(A)+q(N(A))]
     = min_A[ L₁(A)+ min_q q(N(A)) ] = min_A[L₁(A)+L₂(N(A))] = LB_min`
(`max ≥ min`). Hence `LB_min ≤ LB* ≤ g`. ∎

---

## 4. Theorem (Sound feasibility certificate)

*With `g` the exact feasibility margin (pair feasible iff `g≥1−ε`):*

- *if `LB ≥ 1−ε` for any sound lower bound `LB∈{LB_min,LB(q*),LB*}`, the pair
  is **ε-feasible** (sound `True`);*
- *if `UB < 1−ε`, the pair is **ε-infeasible** (sound `False`);*
- *otherwise (the bounds straddle `1−ε`) the certificate is inconclusive.*

**Proof.** `LB≥1−ε` and `LB≤g` (Theorem 3) ⟹ `g≥1−ε` ⟹ feasible (Theorem V.3).
`UB<1−ε` and `g≤UB` ⟹ `g<1−ε` ⟹ infeasible. ∎

This is the certificate the lazy method lacks: lazy used an **upper** bound (the
LP dual) to certify feasibility, which Theorem 3 forbids (`UB≥1−ε` proves
nothing about `g`). A sound `True` requires a **lower** bound, supplied here.

---

## 5. Proposition (the gap is a minimax / saddle-point gap)

*`UB − LB* ≥ 0` always. The gap `g − LB*` equals the minimax gap of the
zero-sum game with minimizer `c∈C`, maximizer `q∈P₂`, payoff `Φ(c,q)`.*
*Equivalently, `LB* = g` (gap zero) **iff** there exists a "universal" coarse
marginal `q*∈P₂` with `min_{c∈C}Φ(c,q*) = g` — a single `q*` whose worst fine
corner is exactly the global worst corner (a saddle point `(c*,q*)` of `Φ`).*

**Proof.** `g = min_c max_q Φ(c,q)` and `LB* = max_q min_c Φ(c,q)` (substitute
`Φ=min_A f` and commute the `min_A` with `min_c` / `max_q`). These are the two
sides of the `(c,q)`-minimax; weak minimax gives `LB* ≤ g`. Equality holds iff
the game has a saddle point `(c*,q*)`: `max_q Φ(c*,q) = Φ(c*,q*) = min_c
Φ(c,q*)`, i.e. a `q*` whose minimizing corner `c*` attains `g`. ∎

**Remark (gap can be nonzero).** `Φ(c,q)=min_A[c(U\A)+q(N(A))]` is a pointwise
minimum of affine functions of `c` and also of `q`, hence **concave in both**
`c` and `q`. Sion's minimax theorem requires convex–concave; a concave–concave
game need not have a saddle point. The toy instance in `lazy_enum_lower_bound_
theory.md` (`g=0.80, LB*=0.50, UB=1.00`) exhibits a nonzero `0.50` gap
concretely. Hence strong duality is **not** available in general — consistent
with §3 of `Competitive_Approximate_Relation_Computation.md` (no cheap
elimination of corner enumeration in the worst case).

---

## 6. Corrections to the informal theory doc

Writing the proof formally exposed two errors in
`lazy_enum_lower_bound_theory.md`. Both affect **efficiency claims only**; the
**soundness** results above are unaffected.

### Correction 1 — Lower-bound closed forms need nonzero lowers

The informal doc stated `L₁(A)=max(0,1−Σ_{i∈A}û_i)`, `L₂(S)=max(0,1−Σ_{j∉S}û²_j)`.
These are the **zero-lower-bound special case**. The general IMDP has nonzero
lowers; the correct forms (Lemma 2) are

```
L₁(A) = max(Σ_{i∈U\A} l̂_i , 1 − Σ_{i∈A} û_i),
L₂(S) = max(Σ_{j∈S} l²_j , 1 − Σ_{j∉S} û²_j).
```

The toy validations used `l=0`, so they did not catch this. **Action**: the
implementation must use the general forms; the informal doc must be updated.

### Correction 2 — The bounds are NOT submodular; polynomial time is OPEN

The informal doc claimed each bound is a submodular set function of `A`, hence
polynomial-time via submodular minimization. **This is false.** `L₁(A)` is the
positive part of a modular-decreasing function, which is **supermodular**, not
submodular:

> *Counterexample.* `U={1,2}`, `l̂=0`, `û=(1,1)` (so `P₁` is the full simplex).
> Take `q*=(½,½)` on `V={a,b}` with `R={(1,a),(2,b)}`. Then
> `L₁(∅)=1, L₁({1})=L₁({2})=0, L₁({1,2})=0` and the coverage term
> `q*(N(·))` gives `0,½,½,1`. So `F=L₁+q*(N(·))` satisfies
> `F({1})+F({2})=1.0 < 2.0=F({1,2})+F(∅)`, the **super**modular inequality. ∎

Since `q*(N(A))` is a (submodular) coverage function and `L₁` is supermodular,
their sum is **neither** submodular nor supermodular in general. Generic
non-submodular set-function minimization is NP-hard. Therefore:

- The **polynomial-time-via-submodular-minimization** argument is **retracted**.
- Each bound is still **exact** as `min_{A⊆U}` over all `2^{k₁}` subsets, and
  is **LP-free** (each subset costs `O(k₁)` arithmetic, no LP solve).
- Brute force is `O(2^{k₁}·k₁)`, the **same exponent** as corner enumeration but
  **without LPs** (LPs were ≈95% of runtime) — a constant-factor win, not a
  complexity-class improvement.
- Whether a **polynomial** algorithm exists (e.g. via an LP relaxation of the
  subset problem, or a tailored combinatorial algorithm exploiting the
  `L₁+coverage` structure) is **open** — left to future work (§8).

This does **not** weaken the formal-methods guarantee: soundness (Theorems 3–4)
is independent of how the bounds are computed. It only revises the speed
expectation: the bounds are a fast, **LP-free, sound** pre-filter/certificate,
not a proven poly-time exact method.

---

## 7. Relation to the §3 barrier (no contradiction)

§3 of `Competitive_Approximate_Relation_Computation.md` states corner
enumeration cannot be eliminated in the worst case. This theorem is consistent:

- When the minimax gap is nonzero **and** the bounds straddle `1−ε`
  (Theorem 4, inconclusive case), deciding still requires enumeration — worst
  case unchanged.
- The novelty is: (i) a **sound lower bound** always exists (certifies
  feasibility without enumerating corners whenever it clears `1−ε`), and
  (ii) a **characterized subclass** — existence of a universal coarse marginal
  (Proposition 5, gap=0) — where the pair is decidable **exactly, without LPs**.
- The lower bound never produces an unsound answer; when it cannot decide, the
  exact Theorem V.3 enumeration remains the fallback. Soundness of the final
  `ε`/`R` is therefore **never below** that of the original algorithm.

---

## 8. Open questions (for Step 2+)

1. **Poly-time computation of the bounds.** Is there an LP/combinatorial
   relaxation of `min_A[L₁(A)+q*(N(A))]` with small integrality gap? (The
   structure is "supermodular-decreasing + coverage"; prize-collecting-style
   relaxations may apply.) Open.
2. **`q*` selection.** Best `q*` for `LB(q*)` tightness; candidate = the `μ₂`
   returned by one primal coupling LP on the initial hard corner. To test.
3. **Gap frequency on real benchmarks.** How often is `LB* = g` (universal
   coarse marginal exists) on Test1D / DoubleIntegrator / Dubins? Decides how
   often the bounds alone settle the pair. Step 2 instrumentation.
4. **Tight lower bound without fixing `q*`.** `LB_min` is parameter-free but
   weak; can a cheap non-trivial improvement be derived?

---

## 9. Summary of what is now proven

| Statement | Status |
|---|---|
| `Φ(p,q)=min_A[p(U\A)+q(N(A))]` (max-flow min-cut) | **Proven** (Lemma 1) |
| Closed forms for `L₁,L₂,U₂` (general, nonzero lowers) | **Proven** (Lemma 2) |
| `LB_min ≤ LB(q*) ≤ LB* ≤ g ≤ UB` (sound bracketing) | **Proven** (Theorem 3) |
| `LB≥1−ε ⟹ feasible`, `UB<1−ε ⟹ infeasible` | **Proven** (Theorem 4) |
| Gap = minimax/saddle gap; `=0` ⇔ universal coarse `q*` | **Proven** (Prop. 5) |
| Gap can be nonzero (concave–concave; toy `0.50`) | **Shown** |
| Bounds are submodular ⇒ poly-time | **RETRACTED** (Corr. 2) |
| Bounds exact, LP-free, `O(2^{k₁}k₁)` | **Proven** |
| Poly-time computation of bounds | **OPEN** |
| Final `ε`/`R` never less rigorous than Theorem V.3 (with fallback) | **Proven** (§7) |

The keystone — **soundness** — is rigorous. The open question is **speed**.
