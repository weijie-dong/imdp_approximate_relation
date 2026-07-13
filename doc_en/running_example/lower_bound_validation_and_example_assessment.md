# Running-Example Validation of the Lower-Bound Theory & Example Assessment

> Records (1) the programmatic validation of the sound lower-bound theory
> (`formal_lower_bound_theorem.md`) on the paper's running example, (2) a
> computation bug caught by that validation and its fix, and (3) an assessment
> of whether the two running examples are well-designed for illustrating the
> definitions and computation flow. Material may be reused in the paper.
>
> Script: `validate_lower_bound_running_example.py` (run with the `dyabstract`
> env). Theory: `../lazy_enum_review/formal_lower_bound_theorem.md`.

---

## 1. Setup (the running example)

Two 3-state IMDPs (see `example_description.md`):
- `M1 = {p1,q1,r1}`, actions `{α,β}`; `M2 = {p2,q2,r2}`, actions `{γ,δ}`.
- Candidate relation `R = {(p1,p2),(q1,q2),(r1,r2)}`.
- The only non-trivial pair is `(p1,p2)`; `(q1,q2)`,`(r1,r2)` are self-loops.
- `P2(p2,γ)` is tuned by `t` (upper bound `0.6+t`); the document sets `t=ε`.

For each sub-pair `(p1,a1,p2,a2)` we compute, with `U={q1,r1}` (k1=2),
`V={q2,r2}`, `R` on successors `={(q1,q2),(r1,r2)}` (diagonal):

```
g      = min_{c in C(P1)} max_{q in P2} Φ(c,q)    exact (max-flow min-cut + LP)
UB     = min_A [ L1(A) + U2(N(A)) ]               sound upper bound
LB*    = max_{q* in P2} min_A [ L1(A) + q*(N(A)) ] tightest sound lower bound
LB_min = min_A [ L1(A) + L2(N(A)) ]               parameter-free lower bound
```

`ε ∈ {0, 0.2, 0.5}`; the pair is feasible iff `g ≥ 1−ε`. We check the bracket
`LB_min ≤ LB* ≤ g ≤ UB` (Theorem 3) and the sound certificate (Theorem 4):
`LB*≥1−ε ⟹ FEASIBLE`, `UB<1−ε ⟹ INFEASIBLE`, else `inconclusive`.

---

## 2. Bug caught by validation (and fix)

The first version computed `g` and `LB*` by scanning the **coarse corners** of
`P2`. This is **wrong**: `Φ(c,q)` and `LB(q*)` are **concave** in `q`, so their
maximum over `P2` is a **concave maximization** whose optimum can lie in the
**interior** of `P2`, not at a vertex.

Concrete instance — sub-pair `(p1,β,p2,δ)`, `t=0.5`:
- `P2(p2,δ) = {q2∈[0.1,0.8], r2=1−q2}` — a 1-D segment with corners
  `(0.1,0.9)` and `(0.8,0.2)`.
- For fine corner `c=(0.6,0.4)`, the optimal coarse marginal is `q*=(0.6,0.4)`,
  which is **interior** to `P2`; it yields `Φ=1.0`. Both coarse corners yield
  only `0.5` and `0.8`. So a corner scan returns `M(c)=0.8` (wrong); the true
  value is `1.0`.
- Similarly the true `LB*` is `0.7` (attained at interior `q*=(0.3,0.7)`), not
  `0.5` (max over corners).

**Fix** (in `validate_lower_bound_running_example.py`): compute `M(c)` and
`LB*` as **LPs** over the whole `P2` (not corner scans):
- `M(c)` = the joint coupling LP `max_{W,q} W(R) s.t. marginals, q∈P2`.
- `LB*` = `max_{q*,t} t s.t. t ≤ L1(A)+q*(N(A)) ∀A, q*∈P2` (a concave-max
  written as an LP with `2^{k1}` constraints).

`UB` and `LB_min` were already correct: they use the linear extremal-mass
closed forms `U2(S)=max_q q(S)`, `L2(S)=min_q q(S)` (linear ⇒ attained at
corners ⇒ closed form valid).

**Lesson**: validation on a non-trivial case immediately exposed an
implementation error that the formal proof (which correctly writes
`max_{q∈P2}`, not "max over corners") does not. This is exactly why Step 2
(real-benchmark validation) is required before trusting any implementation.

---

## 3. Validation results (clean run)

Bracket `LB_min ≤ LB* ≤ g ≤ UB` holds on **all 12** sub-pairs
(`3 values of t × 2×2 actions`); `g−UB` is within `±3×10⁻⁹` (LP numerical
noise). **Every certificate is sound** — no false-feasible, no false-infeasible.

### 3.1 Per sub-pair bounds (t=0.5; t=0.2 and t=0.0 are qualitatively similar)

| sub-pair `(a1,a2)` | `g` | `UB` | `LB*` | `LB_min` | gap `UB−LB*` |
|---|---|---|---|---|---|
| `(α,γ)` | 1.0 | 1.0 | 0.75 | 0.10 | 0.25 |
| `(α,δ)` | 1.0 | 1.0 | 0.75 | 0.30 | 0.25 |
| `(β,γ)` | 0.9 | 0.9 | 0.70 | 0.00 | 0.20 |
| `(β,δ)` | 0.9 | 0.9 | 0.70 | 0.20 | 0.20 |

Observations: `UB = g` on **every** sub-pair (the upper bound is tight here);
`LB*` is strictly below `g` (nonzero gap) on every sub-pair — the disjunction
is active throughout. The hard sub-pair `(β,δ)` is the paper's worked example
(corner `(0,1)`, `μ2=(0.2,0.8)`); its `g=0.9` drives the cooperative/competitive
contrast below.

### 3.2 Sound certificate vs ground truth, across `ε` (sub-pair `(β,δ)`, `t=0.5`)

| `ε` | truth (`g≥1−ε`?) | certificate | sound? |
|---|---|---|---|
| 0.0 | infeasible (`0.9<1`) | `INFEASIBLE(UB)` (`UB=0.9<1`) | ✓ |
| 0.2 | feasible (`0.9≥0.8`) | `inconclusive` (`LB*=0.7<0.8`, `UB=0.9≥0.8`) | ✓ (no false claim) |
| 0.5 | feasible (`0.9≥0.5`) | `FEASIBLE(LB)` (`LB*=0.7≥0.5`) | ✓ |

This is the honest picture: at `ε=0.2` the bounds **cannot** certify
feasibility even though the pair is truly feasible — the gap leaves it
inconclusive, and enumeration would be required. At `ε=0.5` the lower bound
**does** certify. At `ε=0` the upper bound certifies infeasibility.

### 3.3 Disjunction made concrete (sub-pair `(β,δ)`)

The gap `g−LB*=0.2` exists because the optimal coarse marginal depends on the
fine corner:

| fine corner `c` | optimal coarse `q*` (interior of `P2`) | `Φ(c,q*)` |
|---|---|---|
| `(0,1)` | `q*=(0.1,0.9)` (a corner of `P2`) | 0.9 |
| `(0.6,0.4)` | `q*=(0.6,0.4)` (**interior** of `P2`) | 1.0 |

No single `q*` is simultaneously optimal for both corners ⇒ minimax gap ⇒ the
lower bound cannot reach `g`. This is exactly the §3.3 disjunction
(`Competitive_Approximate_Relation_Computation.md`), on a 3-state example.

### 3.4 Cross-check vs the paper's analytical conclusions

| Scenario | Paper conclusion | Validation |
|---|---|---|
| Cooperative `ε=0` (`t=0`) | `(p1,p2)` **removed** | ✓ `a1=β`: `best_g=0.9<1` ⇒ `∀a1` fails ⇒ removed |
| Competitive `ε=0` (`t=0`) | `(p1,p2)` **retained** | ✓ both `a2` defended by `a1=α` with `g=1.0` |
| Algorithm 1 `ε=0.2` (`t=0.2`) | retained | ✓ `∀a1 ∃a2 g≥0.8` |
| Algorithm 2 `ε=0.5` (`t=0.5`) | retained | ✓ `∀a2 ∃a1 g≥0.5` |

All four match. The `g` values reproduce the paper's hand-derived coupling
masses (e.g. `W(R)=0.9` with `μ2=(0.1,0.9)`, `W(R)=1.0` with `μ2=(0.6,0.4)`).

---

## 4. Assessment: are the running examples well-designed?

**Verdict: yes — for illustrating definitions and computation flow.** Minimal,
clean numbers, sharp contrasts. Specifics:

### 4.1 Strengths (keep)

- **The corner `(0,1)` of `(p1,β)` is a textbook hard corner.** It cannot be
  exactly matched (cooperative `ε=0` removes `(p1,p2)`), but is rescued either
  by relaxing `ε` or by switching to competitive semantics (∃`a1` picks `α`).
  One corner illustrates three things at once: *why corners are necessary*,
  *why `ε` is necessary*, and *the `∀a1` vs `∃a1` quantifier difference*.
- **Cooperative-vs-competitive contrast on the same pair.** `(p1,p2)` is
  removed under cooperative `ε=0` but retained under competitive `ε=0` — the
  cleanest possible illustration of the quantifier-order difference
  (`∀a1∀μ∃a2∃μ` vs `∀a2∃a1∀μ∃μ`).
- **Clean numbers.** `0.1/0.6/0.8/0.9`, `g∈{0.8,0.9,1.0}` — paper-friendly.
- **`ε`-relaxation visible.** `ε=0/0.2/0.5` shows the slack lifting a pair
  from infeasible to feasible.

### 4.2 Weaknesses / optional revisions

1. **Corner count is always 2.** Every `(s,a)` has `k1=2` successors ⇒ 2
   corners. The "corner enumeration is the bottleneck" motivation — the entire
   reason for lazy enumeration and the lower bounds — is **invisible** at
   `k1=2`. Fine for definitions/flow; insufficient to motivate the bounds.
   *Recommendation*: keep the `k1=2` example for definitions; add **one**
   `k1=3` sub-example (4 corners, 8 subsets `A⊆U`, non-trivial `N(A)`) to make
   the subset-minimization and neighborhood structure visible. (Delivered in
   `k1_3_subexample.py`.)
2. **Coarse side is always `k2=2`.** The `β` convex-combination of coarse
   corners (Definition 5) is never exercised non-trivially (`P2` is a 1-D
   segment). Acceptable for a running example; the case study covers scale.
3. **`t=ε` coupling.** Elegant (lets `M2` be ε-subsumed by `M1` at the right
   `ε`), but may blur "approximation tolerance `ε`" vs "model parameter `t`".
   *Recommendation*: state explicitly in the paper that `t=ε` is a convenience
   and the two are independent in general.
4. **Fixed-point iteration is trivial** (one interesting pair ⇒ one
   iteration). Does not illustrate cascading refinement. Not the goal of a
   "definitions/flow" example, so acceptable.

### 4.3 Suitability for illustrating the lower bounds

The running example is **well-suited** to illustrate the bounds, with one
caveat:
- It shows the **bracket**, a **tight upper bound** (`UB=g` everywhere), a
  **nonzero gap** with a **concrete cause** (corner-dependent optimal `q*`),
  and **both** a successful lower-bound certificate (`ε=0.5`) **and** an
  inconclusive case (`ε=0.2`).
- Caveat: at `k1=2` the subset minimization is over only 4 subsets, so the
  *combinatorial* nature of the bound is not visible. The `k1=3` sub-example
  (4.2.1) fills this gap.

---

## 5. Artefacts

- `validate_lower_bound_running_example.py` — the validator (LP-correct
  `g`/`LB*`, closed-form `UB`/`LB_min`).
- `k1_3_subexample.py` — the `k1=3` sub-example (Task a).
- `paper_ready_running_example_table.md` — paper-formatted tables/figure text
  (Task b).
- This file — analysis + assessment (Task 1).
