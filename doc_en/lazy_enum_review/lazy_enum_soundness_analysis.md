# Lazy Enumeration Soundness: Detailed Theory Analysis

> Companion to `lazy_enum_bugs_and_theory_review.md`. Goal: settle Q1/Q2 from
> that doc with a precise derivation, then reconcile the contradiction between
> `Competitive_Approximate_Relation_Computation.md` §3 (theory) and
> `lazy_enum_and_optimizations.md` §2.3/§8.6 (feature doc).
>
> **Bottom line up front:** the max-mass coupling dual gives an **upper bound**
> on `M(p)`. Upper bounds can certify *infeasibility* of a corner but **never**
> *feasibility*. Therefore "separation produced no new corner ⇒ all corners
> feasible" is **not a valid certificate**. The lazy method is sound only as a
> *violator-finder* (returns `False` correctly); returning `True` is a heuristic
> unless backed by full enumeration. This matches the theory doc §3.

---

## 1. Setup and notation

- Fine interval polytope
  `P₁ = P(x₁,a₁) = { p ∈ ℝ^k : Σ_i p_i = 1, p̂_lower_i ≤ p_i ≤ p̂_upper_i }`
  (box-constrained simplex). `C = vertices(P₁)` — finitely many, ≤ `2^(k−1)`.
- For a corner `c ∈ C` the **coupling LP** (max-mass form, as implemented in
  `coupling.py:check_coupling_max_mass`):

  ```
  M(c) = max_{W,β}  Σ_{(i,j)∈R} W[i,j]
         s.t.  Σ_j W[i,j] = c_i                  (fine marginal, i=1..k1)
               Σ_i W[i,j] = (β·V₂)[j]            (coarse marginal)
               Σβ = 1, β ≥ 0, W ≥ 0
  ```

- `c` is feasible ⟺ `M(c) ≥ 1 − ε`.
- The pair `(x₁,x₂,a₁,a₂)` is feasible ⟺ `∀ c ∈ C: M(c) ≥ 1−ε`
  ⟺ `min_{c∈C} M(c) ≥ 1−ε`.

`S_{a₂} = { μ₁ : ∃ feasible coupling }` is a convex polytope (projection of an
LP region; theory doc §3.1). Feasibility of the pair is the inclusion
`P₁ ⊆ S_{a₂}`, and by Minkowski–Weyl (§3.2)

```
P₁ ⊆ S_{a₂}  ⟺  C ⊆ S_{a₂}  ⟺  min_{c∈C} M(c) ≥ 1−ε.
```

So the quantity we must certify is **`g := min_{c∈C} M(c) ≥ 1−ε`**.

---

## 2. M(p) is concave; the dual is an upper bound

Take the dual of the coupling LP. Let `α_i` (free) be the dual of the fine
marginal equality `Σ_j W[i,j] = c_i`, `γ_j` (free) of the coarse marginal, and
`σ` (free) of `Σβ = 1`. Standard max-LP duality gives

```
M(p) = min_{(α,γ,σ) ∈ D}  [ pᵀα + σ ],
```

where `D` is the dual-feasible set (reduced-cost conditions `α_i + γ_j ≥ 1_{(i,j)∈R}`
for `W ≥ 0`, plus the `β ≥ 0` conditions; their exact form is irrelevant here).
Two facts follow immediately:

1. **M is concave in p.** It is the pointwise minimum of affine functions
   `p ↦ pᵀα + σ`, hence concave (and piecewise-linear). Therefore its minimum
   over the polytope `P₁` is attained at a vertex — this is *why* corners
   suffice (§3.2).
2. **Any fixed dual gives an upper bound.** For every `(α*,σ*) ∈ D` and every
   `p ∈ P₁`:

   ```
   M(p) ≤ pᵀα* + σ*.                                   (UB)
   ```

   The optimal dual at a checked corner `c` is tight there
   (`M(c) = cᵀα_c + σ_c`) and `α_c` is a supergradient of `M` at `c`.

This is the error in the lazy doc §2.3: it writes `M(p) ≥ pᵀα* + τ*`. The
correct relation is `≤` (UB above). The doc's entire feasibility certificate
is built on the reversed inequality.

---

## 3. Upper bounds certify infeasibility, not feasibility

Suppose we hold a dual `(α*,σ*) ∈ D` and the separation LP returns the corner

```
c* ∈ argmin_{p ∈ P₁} (pᵀα* + σ*).
```

Because `(UB)` holds for all `p`, in particular `M(c*) ≤ c*ᵀα* + σ*`.

- **Infeasibility certificate (sound).** If `c*ᵀα* + σ* < 1−ε`, then
  `M(c*) < 1−ε`, so `c*` is a violating corner ⟹ the pair is infeasible ⟹
  return `False`. ✓ This is exactly what the lazy code relies on, and it is
  correct. (The code additionally *verifies* `c*` by re-solving the primal LP,
  which is even safer for the `False` path.)

- **No feasibility certificate.** If `c*ᵀα* + σ* ≥ 1−ε`, we learn nothing:
  `M(c*)` could be above or below `1−ε`. An upper bound being `≥ 1−ε` does not
  force `M(c*) ≥ 1−ε`. Concretely the upper-bound *model*

  ```
  M̂(p) := min_{(α,σ) ∈ collected} (pᵀα + σ)   ≥   M(p)
  ```

  satisfies `min_{p} M̂(p) ≥ min_{p} M(p) = g`. So `min M̂ ≥ 1−ε` (what the
  method effectively observes at termination) **does not imply** `g ≥ 1−ε`. A
  violating corner `u` with `M(u) < 1−ε ≤ M̂(u)` can coexist with a loose
  upper-bound model, simply because the dual `y_u` that separates `u` (Farkas)
  has not been collected.

**This is the unsoundness.** Termination ("separation with the best collected
dual returns an already-checked corner") means `min M̂ ≥ 1−ε`, *not* `g ≥ 1−ε`.

---

## 4. The exact characterization — and why it still yields only an upper bound

One might hope to compute `g` exactly via duality. Interchange the two mins
(valid: `min_{c∈C} min_{d∈D} f(c,d) = min_{d∈D} min_{c∈C} f(c,d)`):

```
g = min_{c∈C} M(c)
  = min_{c∈C} min_{(α,σ)∈D} (cᵀα + σ)
  = min_{(α,σ)∈D}  [ σ + min_{c∈C} cᵀα ]
  = min_{(α,σ)∈D}  [ σ + sep(α) ],
```

where `sep(α) := min_{c∈C} cᵀα` is exactly the separation LP. So the lazy
method's per-dual quantity `σ_d + sep(α_d)` is a **valid upper bound on `g`**
for every collected dual `d`, and `min` over collected duals is a tighter
upper bound, monotonically non-increasing as duals accumulate.

But an **upper bound on `g` cannot certify `g ≥ 1−ε`** — it can only certify
`g < 1−ε` (infeasibility) when some collected dual drives it below `1−ε`.

To certify `g ≥ 1−ε` we would need a **lower bound** on `g`, i.e. a lower bound
on `min_{(α,σ)∈D} [σ + sep(α)]`. That requires showing *no* dual in the entire
feasible set `D` achieves `σ + sep(α) < 1−ε`. By Farkas (theory doc §3.4), the
duals that can separate corners form a cone whose **extremal rays** can be
exponential in number — as large as `|C|` itself. Controlling all of `D` is
worst-case equivalent to enumerating all corners. **There is no cheap lower
bound.** This is precisely the barrier §3.3–§3.4 states.

So the dual characterization, while exact in principle, does not yield a
polynomial feasibility certificate — consistent with §3's conclusion that
corner enumeration cannot be eliminated.

---

## 5. Reconciling the two documents

| Claim | Source | Verdict |
|---|---|---|
| Corner enumeration is necessary; LP duality cannot remove it (worst case). | theory doc §3.2–§3.4 | **Correct.** |
| Lazy enumeration must "find the maximally violating corner **or prove none exists**"; separation LP is "tractable". | theory doc §4.2 | **Correct, if read carefully:** tractable = finds a *candidate*; "prove none exists" is the hard half and is **not** claimed to be cheap. |
| `M(p) ≥ pᵀα* + τ*`; at convergence `∀ unchecked p: M(p) ≥ … ≥ 1−ε`. | lazy doc §2.3 | **Wrong.** Inequality is reversed (`≤`); convergence gives `min M̂ ≥ 1−ε`, not `g ≥ 1−ε`. |
| `converged` ⇒ sound (dual certificate). | lazy doc §8.6, §8.7 table | **Wrong.** Dual certifies infeasibility only. |
| `max_iter` ⇒ potentially unsound (false feasible). | lazy doc §8.7 | **Correct** — but the *same* unsoundness applies to `converged`, not only `max_iter`. |

The contradiction is entirely in the lazy feature doc. The theory doc is
self-consistent: it never claims a cheap feasibility certificate, and §4.2's
"prove none exists" is exactly the step the implementation skips.

---

## 6. What a sound "lazy" would require, and the honest options

The cutting-plane loop is **sound on the `False` side** (any violating corner
it actually generates is correctly reported). The problem is exclusively the
`True` side. Three honest framings:

- **(a) Heuristic + full-enumeration fallback.** Declare `True` only
  provisionally ("no violator found in budget"); to obtain a guaranteed result,
  fall back to full corner enumeration (or the sound `_enumerate_greedy`/
  halfspace path) for the `True` decision. Speedup is preserved on the
  infeasible pairs (the common case when refining `R`); exactness is bought
  back where needed. **Recommended framing.**

- **(b) Exact-but-worst-case-full-enumeration.** Keep generating corners until
  *every* vertex of `P₁` has been checked, then return `True`. This is sound
  but offers no worst-case speedup (§3): termination-on-"no new corner" is
  unsound precisely because "no new corner *generated*" ≠ "all corners
  *checked*". To be sound the loop must guarantee coverage of `C`, which is
  full enumeration.

- **(c) A genuine lower bound on `g`.** Would require controlling the full
  dual cone `D` (§3.4) — exponential, i.e. equivalent to corner enumeration.
  **Not available as a cheap certificate**, per §3.

Given §3, **(a)** is the only framing that is both honest and practically
useful. The current code/doc present the method as **(b)-exact**, which it is
not.

---

## 7. Implications for Q1/Q2/Q3 (from the bug record)

- **Q1 (can dual upper bounds certify feasibility?)** — **No.** Settled by
  §3 above. The max-mass dual is an upper bound; only infeasibility is
  certifiable. Adopt framing **(a)**.
- **Q2 (when may the loop return `True`?)** — Only when either (i) full
  enumeration of `C` has been completed, or (ii) a full-enumeration fallback
  has ratified the provisional `True`. "Separation returned a checked corner"
  is **not** a sufficient condition and must stop being treated as one.
- **Q3 (`best_dual_alpha` role)** — It selects the tightest *upper bound*,
  which improves the *violator-finding* efficiency (more likely to generate a
  real violating corner) but **does not change** the Q1/Q2 conclusion: it
  cannot make termination sound. Keep it as a heuristic for corner generation;
  do not advertise it as part of a certificate.

---

## 8. Minimal correctness-preserving redesign (sketch, for later)

Once framing (a) is agreed:

1. Separation LP: fix Bug A (`reversed(order)` → `order`) so it actually
   targets the most-violating corner — improves the violator-finder.
2. Termination: introduce an explicit flag `fully_enumerated` (true only when
   `|checked| == |C|` via the sound enumerator). Return `True` *guaranteed*
   only when `fully_enumerated`; otherwise return `True` with
   `status='heuristic_no_violator'` and let the caller decide on fallback.
3. `max_iter` exhaustion → return `False`-conservative (require fallback),
   not silent `True`.
4. Doc rewrite (Bug C) to match §3: dual = infeasibility certificate;
   feasibility requires enumeration or fallback; drop "exact" claims for the
   `True` path.

This keeps the speedup where it is real (infeasible pairs, which dominate
during `R`-refinement) and restores exactness via fallback where the cheap
certificate does not exist.
