# Fixing the Lazy Method — and Alternatives When Full Enumeration Is Too Slow

> **⚠️ CORRECTION (read first).** Two errors below are superseded by the
> "ε is the output" re-framing (see `STATUS_AND_ROADMAP.md` §2.6):
> 1. The "(b) sound-but-incomplete / LB-as-primary-test" option (§3) is
>    **retracted**. It is only effective at *large* ε, but large ε means the
>    relation is *meaningless* (`degradation→1`, bound clamps to 0). The useful
>    regime is *small* ε (close systems), where `LB` has a gap and (b)
>    **collapses** (drops the feasible pairs you want to keep). So (b) is not a
>    viable compromise.
> 2. "exact, poly, LP-free" (§3, line ~63) — the **poly** claim is retracted
>    (submodularity failed; see `formal_lower_bound_theorem.md` §6, Corr. 2).
>    Bounds are exact + LP-free but `O(2^{k1})`.
>
> What remains valid: **(a) the tiered design (bounds pre-filter + enumeration
> fallback) is sound + complete** — an *exact acceleration*, not a correctness
> compromise. It speeds up the **easy parts** (infeasible side via `UB<1−ε`;
> large-ε binary-search iterations via `LB`). It does **not** escape enumeration
> for the **tight-ε feasible core** (close systems, the useful regime): there
> `g` must approach 1, `LB` has a gap, and sound certification requires full
> corner enumeration (the §3 barrier). The shipped `lazy` was unsound exactly
> on this hard part.

> Directly addresses: *"full enumeration is too slow, so I tried lazy; you say
> lazy is buggy — can we fix it? If not, what else?"*
>
> Builds on `lazy_enum_lower_bound_theory.md` (sound lower bound) and
> `lazy_enum_soundness_analysis.md` (why the dual upper bound cannot certify
> feasibility). Read those first.

---

## 1. What can and cannot be fixed in the current lazy method

Split the lazy loop into its two decision paths:

| Path | What it does | Sound? | Fixable by patching? |
|---|---|---|---|
| **False path** (violator found) | Generates a corner, solves the primal coupling LP, if `M(c)<1−ε` returns `False` | **Yes** | Yes — fix Bug A (`reversed(order)`) so it actually targets the *most* violating corner. |
| **True path** (`converged`) | "Separation returned an already-checked corner ⇒ all corners feasible" | **No** | **No.** This is not a bug to patch — it is the *wrong certificate*. The dual is an **upper** bound; an upper bound `≥ 1−ε` cannot prove `g ≥ 1−ε` (§3 of the theory doc). No tweak to `best_dual_alpha`, `max_iter`, or the separation sign makes an upper bound certify feasibility. |

**Conclusion**: the lazy method as an *exact* algorithm is **not repairable** on
the True side. But its *violator-search engine* is sound and worth keeping.

---

## 2. The fix: replace the True-side certificate with the lower bound

The lower-bound theory gives the missing sound `True`. The repaired
`check_coupling` per pair becomes a **tiered, all-sound** procedure:

```
1. (cheapest, LP-free)  LB := LB_min                           # or LB(q*) with a cheap q*
   if LB >= 1 - eps : return FEASIBLE       (sound True)
   if UB <  1 - eps : return INFEASIBLE     (sound False, UB from §3 of lower-bound doc)

2. (fast, sound False)  lazy violator-search (Bug A fixed):
   run the cutting plane as a VIOLATOR FINDER only.
   if it finds a corner with M(c) < 1 - eps : return INFEASIBLE   (sound False)

3. (residual, exact)    full corner enumeration (greedy/halfspace, sound):
   decide exactly.
```

Properties:
- Every returned answer is **sound** (no false feasible, no false infeasible).
- The expensive tier-3 enumeration is reached **only when the bounds straddle
  `1−ε` AND lazy found no violator** — the residual. On most pairs tier 1 or 2
  decides.
- Tier 1 is **LP-free** (submodular minimization), so for large `k1` it can be
  far cheaper than even one corner LP, let alone `2^k1` of them.

This is strictly better than the current code: same speed on the cases lazy
already handles, sound where it was wrong.

---

## 3. Alternatives if even tier-3 fallback is too slow

If the residual set is still too large, the lower bound itself becomes the
primary tool, not just a pre-filter:

- **LB as the primary feasibility test.** For pairs where the coarse response
  is (near) corner-independent, `LB* = g` and tier 1 alone is **exact, poly,
  LP-free**. Experimentally identify how many pairs fall in this class on
  Test1D / DoubleIntegrator / Dubins. If a large fraction do, enumeration is
  needed only for the rest.
- **Tighter `q*`.** `LB(q*)` tightens with better `q*`. Cheap strategy: solve
  the primal coupling LP **once** on the initial hard corner, take its `μ₂` as
  `q*`. One LP per pair, then LP-free submodular min — vs `2^k1` LPs.
- **Specialized submodular-min.** The objective is `L₁(A) + coverage(A)`,
  a structured form; a custom solver (or branch-and-bound with submodular
  relaxations) may beat generic submodular-min and beat `2^k1` brute force for
  mid-size `k1` (≈16–25).
- **Direct-variableized coarse (§4.1 of the theory doc, already done).**
  Removes coarse-corner dependence from the LP; keep it.
- **ε-search reuse.** During binary search on `ε`, `R` only shrinks, so
  `N(A)` only shrinks ⇒ bounds are monotone in `ε` ⇒ recompute incrementally
  rather than from scratch each ε step.

Honest ceiling: in the **worst case** (gap nonzero, bounds straddle `1−ε`, no
violator found) §3 says enumeration is unavoidable. The lower bound does not
remove that worst case; it **shrinks the set of pairs that hit it** and makes
the rest LP-free. Whether that is enough for your 196→441 case is an empirical
question — but it is strictly more than the current (unsound) lazy gives you.

---

## 4. Recommended next step

Before any code: **instrument** the current pipeline to log, per pair, the
values of `LB_min`, `LB(q*)` (with `q*` = a one-shot primal `μ₂`), `UB`, and
`g` (ground truth via enumeration on small cases). This tells us:

1. How often `LB ≥ 1−ε` (sound True, LP-free) — the free win.
2. How often `UB < 1−ε` (sound False) — pairs the dual already settles.
3. How often bounds straddle (residual needing enumeration) — the real cost.

That data decides whether the tiered fix (§2) is enough, or whether we invest
in the tighter `q*` / specialized solver (§3). It also validates the
lower-bound theory on real benchmarks, not just the toy case in the theory doc.

Only after that measurement do we touch `lazy_enum.py` / `coupling.py`.
