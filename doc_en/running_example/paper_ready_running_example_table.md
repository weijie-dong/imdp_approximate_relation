# Paper-Ready Material: Lower Bounds on the Running Example

> Numbers are machine-verified (`validate_lower_bound_running_example.py`,
> `k1_3_subexample.py`). Lift directly into the paper. Theory in
> `../lazy_enum_review/formal_lower_bound_theorem.md`.

## Notation (one line for the paper)

For a fixed `(s₁,a₁,s₂,a₂)`, let `g = min_{c∈C(P₁)} max_{q∈P₂} Φ(c,q)` be the
worst-corner max-coupling-mass (pair feasible ⇔ `g ≥ 1−ε`), with
`Φ(c,q)=min_{A⊆U}[c(U\A)+q(N(A))]` (max-flow/min-cut). We compute a sound
**upper** bound `UB`, a sound **lower** bound `LB*` (tightest), and a
parameter-free lower bound `LB_min`, satisfying `LB_min ≤ LB* ≤ g ≤ UB`.

---

## Table 1 — Bounds per sub-pair of `(p₁,p₂)` on the running example

`M1`/`M2` as in `example_description.md`; `t=ε` tunes `P₂(p₂,γ)`. Four
`(a₁,a₂)` sub-pairs; `U=V={q,r}`, `R` diagonal.

### (a) `t = 0.5`  (`P₂(p₂,γ): q₂∈[0.1,1.0]`)

| sub-pair `(a₁,a₂)` | `g` | `UB` | `LB*` | `LB_min` | gap `UB−LB*` |
|---|---|---|---|---|---|
| `(α,γ)` | 1.00 | 1.00 | 0.75 | 0.10 | 0.25 |
| `(α,δ)` | 1.00 | 1.00 | 0.75 | 0.30 | 0.25 |
| `(β,γ)` | 0.90 | 0.90 | 0.70 | 0.00 | 0.20 |
| `(β,δ)` | 0.90 | 0.90 | 0.70 | 0.20 | 0.20 |

### (b) `t = 0.2`  (`P₂(p₂,γ): q₂∈[0.1,0.8]`)

| sub-pair `(a₁,a₂)` | `g` | `UB` | `LB*` | `LB_min` | gap `UB−LB*` |
|---|---|---|---|---|---|
| `(α,γ)` | 1.00 | 1.00 | 0.75 | 0.30 | 0.25 |
| `(α,δ)` | 1.00 | 1.00 | 0.75 | 0.30 | 0.25 |
| `(β,γ)` | 0.90 | 0.90 | 0.70 | 0.20 | 0.20 |
| `(β,δ)` | 0.90 | 0.90 | 0.70 | 0.20 | 0.20 |

### (c) `t = 0.0`  (`P₂(p₂,γ): q₂∈[0.1,0.6]`, exact-match setting)

| sub-pair `(a₁,a₂)` | `g` | `UB` | `LB*` | `LB_min` | gap `UB−LB*` |
|---|---|---|---|---|---|
| `(α,γ)` | 1.00 | 1.00 | 0.75 | 0.50 | 0.25 |
| `(α,δ)` | 1.00 | 1.00 | 0.75 | 0.30 | 0.25 |
| `(β,γ)` | 0.90 | 0.90 | 0.70 | 0.40 | 0.20 |
| `(β,δ)` | 0.90 | 0.90 | 0.70 | 0.20 | 0.20 |

**Caption.** On every sub-pair the bracket `LB_min ≤ LB* ≤ g ≤ UB` holds
(verified to `10⁻⁶`). The upper bound is **tight** (`UB=g` throughout); the
lower bound has a **persistent gap** (`0.15–0.25`) — the disjunction of §3.3 is
active even on a 3-state example.

---

## Table 2 — Sound certificate vs ground truth (the hard sub-pair `(β,δ)`, `t=0.5`)

This is the paper's worked corner `(0,1)` with `μ₂=(0.2,0.8)`.

| `ε` | truth `g≥1−ε`? | `g` | `UB` | `LB*` | certificate | sound? |
|---|---|---|---|---|---|---|
| 0.0 | infeasible (`0.9<1`) | 0.9 | 0.9 | 0.70 | `INFEASIBLE` (`UB<1`) | ✓ |
| 0.2 | feasible (`0.9≥0.8`) | 0.9 | 0.9 | 0.70 | `inconclusive` (`LB*<0.8≤UB`) | ✓ |
| 0.5 | feasible (`0.9≥0.5`) | 0.9 | 0.9 | 0.70 | `FEASIBLE` (`LB*≥0.5`) | ✓ |

**Caption.** The bounds are sound at every `ε` (no false feasible/infeasible).
They **certify** feasibility at `ε=0.5` and infeasibility at `ε=0`, but are
**inconclusive** at `ε=0.2` although the pair is truly feasible — the gap
leaves a residual that only enumeration can decide. This is the honest
completeness limitation, consistent with the §3 barrier.

---

## Figure 1 (suggested) — The disjunction on `(β,δ)`

The gap `g−LB* = 0.2` exists because the optimal coarse marginal depends on the
fine corner:

| fine corner `c` | optimal coarse `q*` (argmax of `Φ(c,·)`) | `Φ(c,q*)` |
|---|---|---|
| `(0, 1)` | `q*=(0.1, 0.9)` — a **vertex** of `P₂` | 0.90 |
| `(0.6, 0.4)` | `q*=(0.6, 0.4)` — **interior** of `P₂` | 1.00 |

No single `q*` is optimal for both corners ⇒ `max_q min_c Φ < min_c max_q Φ`
⇒ `LB* < g`. **Caption:** the disjunction (§3.3) on the running example's
hardest sub-pair: the coarse response must adapt to the fine corner, so a
single dual/certificate cannot cover all corners — the concrete reason the
lower bound is not always tight. (Note `q*=(0.6,0.4)` being interior also shows
why the coarse marginal must be optimized over the whole polytope, not just its
vertices.)

---

## Table 3 — Cross-check against the paper's analytical conclusions

| Scenario | Semantics | `ε` | Paper | Reproduced |
|---|---|---|---|---|
| `(p₁,p₂)` | cooperative (`∀a₁∃a₂`) | 0 | **removed** | ✓ `a₁=β`: `max_a₂ g=0.9<1` |
| `(p₁,p₂)` | competitive (`∀a₂∃a₁`) | 0 | **retained** | ✓ both `a₂` defended by `α` (`g=1.0`) |
| Algorithm 1 | cooperative | 0.2 | retained | ✓ `∀a₁ ∃a₂ g≥0.8` |
| Algorithm 2 | competitive | 0.5 | retained | ✓ `∀a₂ ∃a₁ g≥0.5` |

**Caption.** The computed `g` values reproduce the paper's hand-derived
coupling masses (e.g. `W(R)=0.9` with `μ₂=(0.1,0.9)`; `W(R)=1.0` with
`μ₂=(0.6,0.4)`), and the pair-level retain/remove decisions match all four
scenarios. The same `g=0.9` on the `(β,·)` sub-pairs is what removes
`(p₁,p₂)` under cooperative `ε=0` (where `β` is universally quantified) while
competitive `ε=0` retains it (where `α` is existentially chosen).

---

## Table 4 — `k₁=3` sub-example: making the subset minimization visible

A constructed single-pair check with `k₁=k₂=3`, `R={(0,0),(0,1),(1,1),(2,2)}`
(so `N({0})={0,1}`, `N({1})={1}`, `N({2})={2}`), nonzero lowers on both sides.

| bound | value | attained at |
|---|---|---|
| `g` | 0.90 | corner `c=(0.3,0,0.7)` (and two others give `0.9`; three give `1.0`) |
| `UB` | 0.90 | `A={2}`: `L₁({2})+U₂({2})=0.30+0.60` |
| `LB*` | 0.75 | interior `q*=(0.108,0.442,0.450)` |
| `LB_min` | 0.30 | `A={2}`: `L₁({2})+L₂({2})=0.30+0.00` |
| gap `UB−LB*` | 0.15 | per-corner `q*` differ across all 6 corners |

**Caption.** With `k₁=3` the bound minimizes over `8` subsets `A⊆U` with a
non-trivial neighborhood `N(A)` (shown in the script's per-subset table). The
upper bound is again tight (`UB=g`); the lower bound has gap `0.15`, and the
per-corner optimal `q*` differs across corners (disjunction). `LB*` is attained
at an **interior** `q*`, confirming the coarse marginal must be optimized over
the whole polytope. This is the smallest instance that exposes the
combinatorics the `k₁=2` running example hides.

---

## One-paragraph summary for the paper

> We validate the sound bounds on the running example. On every `(a₁,a₂)`
> sub-pair of `(p₁,p₂)`, the bracket `LB_min ≤ LB* ≤ g ≤ UB` holds; the upper
> bound is tight (`UB=g`), while the lower bound carries a persistent gap
> (`0.15–0.25`) because the optimal coarse marginal is corner-dependent (the
> §3.3 disjunction). The bounds certify feasibility at `ε=0.5` and
> infeasibility at `ε=0` soundly, but are inconclusive at `ε=0.2` for the
> hardest sub-pair `(β,δ)` although it is truly feasible — the residual that
> only enumeration can decide, exactly as the §3 barrier predicts. All
> pair-level retain/remove decisions reproduce the paper's analytical
> conclusions.
