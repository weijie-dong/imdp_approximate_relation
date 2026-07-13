# Lazy Enumeration: Bug Record & Theory Review

> Status: **theory clarification first, code changes deferred.**
> This document records defects found in the lazy corner-enumeration feature
> (`core/approx_sim/lazy_enum.py`, `coupling.py`, and the doc
> `lazy_enum_and_optimizations.md`). The plan is to settle the theoretical
> soundness questions (§1) before touching code (§3), because the most serious
> issue is not a typo but a correctness argument whose conclusion may not hold.

Related docs:
- `lazy_enum_and_optimizations.md` — the feature description (contains the over-claimed soundness argument)
- `Competitive_Approximate_Relation_Computation.md` — the theory; §3 explicitly states LP duality **cannot** eliminate corner enumeration, which is in tension with the lazy doc's "converged ⇒ sound" claim.

---

## 1. Theory questions to settle FIRST

These must be answered before any code fix, because they determine *what* the
code is even supposed to compute.

### Q1. Can dual upper bounds certify feasibility? (No — but the doc claims yes)

The coupling LP for a fixed fine corner `c₁` maximizes in-relation mass:

```
M(c₁) = max_W  Σ_{(i,j)∈R} W[i,j]
        s.t. fine marginal  Σ_j W[i,j] = c₁[i]
             coarse marginal Σ_i W[i,j] = (β·V₂)[j]
             Σβ=1, β≥0, W≥0
```

A pair is feasible for corner `c₁` iff `M(c₁) ≥ 1 − ε`. The pair is feasible
**overall** iff this holds for **every** corner, i.e. `min_{c∈C} M(c) ≥ 1−ε`.

By LP duality, `M(p) = min_{dual-feasible (α,τ)} (pᵀα + τ)`. Therefore for any
fixed dual-feasible `(α*, τ*)`:

```
M(p) ≤ pᵀα* + τ*        (UPPER bound on M(p))
```

Consequences:
- Upper bound `< 1−ε` ⟹ `M(p) < 1−ε` ⟹ corner `p` **violates**. ✅ sound for detecting infeasibility.
- Upper bound `≥ 1−ε` ⟹ **nothing** about `M(p)`. It does **not** certify feasibility.

The lazy doc (`lazy_enum_and_optimizations.md` §2.3, line ~82) writes the
inequality backwards:

> "At convergence, for all unchecked corners p: **M(p) ≥ pᵀα* + τ*** ≥ 1 − ε"

The first `≥` is wrong; it should be `≤`. With the correct direction the chain
proves nothing, so the stated **dual certificate of feasibility does not
exist**. The "converged ⇒ all corners feasible (return True)" step is **not
proven**.

This directly contradicts the project's own theory doc,
`Competitive_Approximate_Relation_Computation.md`:
- §3.2: corner enumeration is "exact and irreversible" — checking `∀ μ₁ ∈ P`
  is equivalent to checking `∀ c ∈ C`.
- §3.3: LP duality gives only a **pointwise** infeasibility certificate
  (Farkas) per corner, **not** a simultaneous certificate over all corners.
- §3.4: enumerating dual extremal rays is worst-case **equivalent** to
  enumerating primal corners — duality cannot remove the enumeration.
- §4.2: the honest requirement for lazy enumeration is "find the corner that
  maximally violates **or prove that none exists**" — and the "prove none
  exists" half is exactly what the upper-bound dual cannot do.

**Open question to settle**: is there *any* valid dual-side certificate of
`min_{c∈C} M(c) ≥ 1−ε` short of full enumeration? Per §3 the answer is no in
the worst case. If we accept that, the lazy method must be re-positioned as
either (a) a **heuristic that is sound on the infeasibility side only**, with
a full-enumeration fallback for the feasibility side, or (b) an exact method
that, in the worst case, degenerates to enumerating all corners (and must
guarantee it does so before returning True).

### Q2. What is the correct separation objective, and what does "convergence" really mean?

The separation subproblem should find the corner most likely to **violate**,
i.e. minimize the dual upper bound: `min_{p∈P₁} pᵀα*`. The corner returned is
a vertex of `P₁`. We then **verify it with the primal coupling LP** (the code
does this part — good: it never trusts the bound to declare feasibility for a
*specific* generated corner).

The unsoundness lives entirely in **termination**: when separation stops
producing *new* corners, the code declares all corners feasible. But
"separation produced no new corner" ≠ "no violating corner remains". A
violating corner `u` with `M(u) < 1−ε` can exist yet never be the argmin of
`pᵀα` for any collected dual `α` (the collected duals are supergradients of
the concave value function `M`; a supergradient-based upper-bound model
`M̂(p) = min_d (pᵀα_d + τ_d) ≥ M(p)` gives `min M̂ ≥ min M`, an upper bound on
the global min — useless for certifying `min M ≥ 1−ε`).

**To settle**: define precisely under what condition the loop may return
`feasible=True`. Candidates:
1. *Full enumeration reached* (every vertex of `P₁` has been checked) — sound,
   but then there is no speedup in the worst case (consistent with §3).
2. *A genuine lower bound on `min_c M(c)`* is computed and shown `≥ 1−ε` —
   requires a dual of a *minimization* reformulation, not the max-mass dual
   currently extracted. Needs derivation; may not exist cheaply.
3. *Treat as heuristic*: return True only as "no violation found within
   budget", never claim exactness; pair with a configurable full-enumeration
   fallback for guarantees.

Q2 depends on Q1. Settle Q1 first.

### Q3. Does the `best_dual_alpha` selection actually help?

`lazy_enum.py` tracks the dual from the corner with the **lowest** `max_mass`
(comment: "tightest upper bound"). For a concave `M`, the dual optimal at the
current min-`M` corner is a supergradient there; using it for separation is
reasonable *as a heuristic for generating promising corners*, but it does not
change the Q1/Q2 conclusion — it cannot turn termination into a sound
certificate. Once Q1/Q2 are resolved we can decide whether to keep, drop, or
redefine this tracking.

---

## 2. Concrete code bugs (verified)

These are independent of the theory debate and are straightforward defects.

### Bug A — Separation LP returns the MAXIMIZER, not the minimizer  [confirmed]

**File**: `core/approx_sim/lazy_enum.py`, `_solve_separation_lp`, lines 49–62.

The objective is `min_p pᵀα` over the box-simplex `P₁`. The greedy fix is: set
all coordinates to `pl`, then distribute the remaining mass `1−Σpl` to the
**smallest-α** coordinates first (up to their `pu`), with one pivot variable.

The code distributes to `reversed(order)` — i.e. the **largest-α**
coordinates first — which **maximizes** `pᵀα`, returning the *least* likely to
violate corner, opposite to the docstring and to §4.2 of the theory doc.

Reproduction (run against the real function):

```
alpha = [0.75, -0.25]     # 0.75 = successor WITH R-partner (good);
                          # -0.25 = successor WITHOUT R-partner (bad)
pl = [0,0], pu = [1,1]

_solve_separation_lp(pl, pu, alpha) -> p = [1, 0],  pᵀα = 0.75   (MAX)
correct min corner          ........   p = [0, 1],  pᵀα = -0.25  (MIN)
```

The CVXPY dual sign was verified separately (standard economic sign: α>0 for
R-partner successors, α<0 for non-R successors), so the sign is not flipped by
the solver — the bug is purely the `reversed()`.

**Impact**: the cutting plane targets easy corners, tends to re-check already
-passing corners, and converges prematurely → false `feasible=True` (R too
large, ε_min underestimated). Same failure class as the corner LP-fallback
warned about in §8.7. Latent on Test1D because `_generate_initial_corner` and
the pre-filter catch the real failures there.

**Fix (deferred)**: change `for idx in reversed(order):` to `for idx in order:`
in the `remaining > 0` branch. (Symmetric care needed for the `remaining < 0`
trim branch — review together.)

### Bug B — Status mislabel on final-iteration break  [minor]

**File**: `core/approx_sim/lazy_enum.py`, line 292.

```python
status = 'converged' if iteration < effective_max_iter - 1 else 'max_iter'
```

If the loop breaks (converges) on the last allowed iteration
(`iteration == effective_max_iter - 1`), this labels it `max_iter` and emits a
spurious warning, while still returning `feasible=True`. Result is unaffected;
only the log/warning is wrong.

**Fix (deferred)**: use an explicit `converged` flag set at every `break`,
rather than inferring from `iteration`.

### Bug C — Doc inequality backwards / over-claimed soundness  [doc]

**File**: `lazy_enum_and_optimizations.md`, §2.3 (line ~82), §8.6, §8.7.

`M(p) ≥ pᵀα* + τ*` should be `M(p) ≤ pᵀα* + τ*`. The "converged ⇒ sound
(dual certificate)" claim in §8.6/§8.7 follows from the wrong inequality and
does not hold (see Q1). The doc even repeats this in the §8.7 table marking
the `converged` case as `✓`.

**Fix (deferred, after Q1 is settled)**: rewrite the soundness section to
match the theory doc §3 — dual gives an infeasibility certificate only;
feasibility requires either full enumeration or a (yet to be derived) valid
lower bound.

---

## 3. Proposed order of work (theory-first)

1. **Settle Q1** — confirm, with derivation, that the max-mass dual cannot
   certify `min_c M(c) ≥ 1−ε`. Cross-check against §3 of the theory doc.
   Decision: which of (a) heuristic + fallback, (b) exact-with-worst-case-full-
   enumeration, (c) find-a-real-lower-bound do we want lazy to be?
2. **Settle Q2** — given (1), write down the exact termination condition under
   which `feasible=True` may be returned, and what guarantee (if any) it
   carries.
3. **Settle Q3** — decide the role of `best_dual_alpha`.
4. *Only then* make code changes:
   - Fix Bug A (`reversed(order)` → `order`), consistent with whatever
     separation semantics Q2 mandates.
   - Fix Bug B (explicit `converged` flag).
   - Fix Bug C (doc rewrite to match the settled theory).
5. Re-run `compare_methods.py` and, crucially, construct a regression case
   where the hardest corner is **not** the initial one and is **not** caught
   by the pre-filter — Test1D does not exercise this path.

---

## 4. Why the Test1D match does not refute the bugs

The lazy and corner methods producing identical `ε_min` and `|R|` on Test1D is
consistent with both Bug A and the Q1 unsoundness being **latent**:

- `_generate_initial_corner` correctly targets the worst case (max mass outside
  R), so the single most likely violator is checked first.
- The pre-filter (`uncoupled mass > ε`) catches outright infeasibility without
  any LP.

In Test1D these two nets catch every real failure, so the (broken) separation
LP never has to find an *additional* violator. The bugs surface only when the
true hardest corner is neither the initial one nor pre-filterable. A dedicated
regression test of that shape is needed before trusting exactness claims.
