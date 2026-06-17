# Interval-Arithmetic Coupling LP via LP Duality

## Problem

Given a fine IMDP state-action pair with probability polytope P1 (defined by
interval bounds `[l_i, u_i]` on k1 successors) and a coarse IMDP state-action
pair with P2 (L corners over k2 successors), we need to check:

> For EVERY valid fine distribution p ∈ P1, does there exist a coupling W and
> coarse mixture β such that ≥ 1-ε mass of W falls within the relation R?

## Current approach (vertex enumeration)

For each corner c1 ∈ vertices(P1), solve the coupling LP:

```
M(c1) = max_{W≥0, β≥0}  Σ_{(i,j)∈R} W[i,j]
        s.t.  Σ_j W[i,j] = c1[i]             (fine marginals)
              Σ_i W[i,j] = Σ_l β_l V2[l][j]  (coarse marginals)
              Σ_l β_l = 1
```

If M(c1) ≥ 1-ε for all c1, the pair survives.  Since M(c1) is concave in c1
(optimal value of a maximization LP is concave in RHS), and P1 is a convex
polytope, the minimum occurs at a vertex.  So checking vertices is exact.
But |vertices| can be ~2^(k1-1), making this exponentially expensive.

## Reformulation via LP duality

The condition is:

```
min_{p ∈ P1} M(p) ≥ 1-ε
```

### Step 1: Dual of the coupling LP (inner)

The coupling LP M(p) (primal, maximization) has dual (minimization):

```
M(p) = min_{α,γ,δ}  p^T α + δ
       s.t.  α_i + γ_j ≥ 1        for (i,j) ∈ R
             α_i + γ_j ≥ 0        for (i,j) ∉ R
             δ ≥ Σ_j γ_j V2[l][j]  for l = 0..L-1
             α_i free, γ_j free, δ free
```

### Step 2: Combine min_p and dual

```
min_{p∈P1} M(p) = min_{p∈P1} min_{α,γ,δ} [p^Tα + δ]   s.t. dual constraints
                = min_{α,γ,δ} [δ + min_{p∈P1} p^Tα]   s.t. dual constraints
```

The inner minimization min_{p∈P1} p^Tα over the interval simplex
P1 = {p : l_i ≤ p_i ≤ u_i, Σp_i = 1} is itself an LP.  Its dual is:

```
min_{p∈P1} p^Tα = max_{μ≥0, ν≥0, λ}  l^Tμ - u^Tν + λ
                  s.t.  μ_i - ν_i + λ = α_i ∀i
```

By strong LP duality (P1 is nonempty when Σl_i ≤ 1 ≤ Σu_i).

### Step 3: Eliminate α

Substitute α_i = μ_i - ν_i + λ into the outer dual:

```
min_{μ≥0, ν≥0, λ, γ, δ}  l^Tμ - u^Tν + λ + δ
s.t.  μ_i - ν_i + λ + γ_j ≥ 1   for (i,j) ∈ R
      μ_i - ν_i + λ + γ_j ≥ 0   for (i,j) ∉ R
      δ ≥ Σ_j γ_j V2[l][j]      for l = 0..L-1
```

### Step 4: Efficient handling of "not in R" constraints

The O(k1·k2) "∉ R" constraints can be reduced to O(k2 + k1) by introducing
γ_min ≤ min_j γ_j:

```
∃ γ_min:  γ_min ≤ γ_j ∀j          (k2 constraints)
          μ_i - ν_i + λ + γ_min ≥ 0 ∀i   (k1 constraints)
```

This is exact: set γ_min = min_j γ_j, then the original constraints hold iff
the reduced ones hold.

## Final single LP

**Variables** (2k1 + k2 + 4): μ[k1] ≥ 0, ν[k1] ≥ 0, λ, γ[k2], γ_min, δ

**Minimize:** l^T μ - u^T ν + λ + δ

**Subject to:**
1. μ ≥ 0, ν ≥ 0
2. γ_min ≤ γ_j for all j
3. μ_i - ν_i + λ + γ_min ≥ 0 for all i
4. μ_i - ν_i + λ + γ_j ≥ 1 for (i,j) ∈ R
5. δ ≥ Σ_j γ_j V2[l][j] for l = 0..L-1

**Feasibility criterion:** optimal value ≥ 1 - ε

## Computational complexity

| | Per-vertex LP (current) | Single dual LP (new) |
|---|---|---|
| #LPs per (a1,a2) | |vertices(P1)| ~ 2^(k1-1) | 1 |
| Variables per LP | k1·k2 + L | 2k1 + k2 + 4 |
| Constraints per LP | k1 + k2 + L + 2 | k1 + k2 + |R| + L |
| Total for k1=13, k2=13, L=100, |R|=50 | 2994 × 20ms ≈ 60s | 1 × ~50ms |

The new formulation eliminates the exponential dependence on the number of
successors, making the approximate simulation algorithm practical for
higher-dimensional systems.

## Relationship to robust optimization

This is an instance of "LP with uncertainty in the RHS" from robust
optimization (Ben-Tal & Nemirovski). The key technique is nesting LP duality
to convert a ∀p∃coupling quantifier into a single LP feasibility check.
The correctness relies on strong LP duality applying at both levels — the
inner coupling LP is always feasible and bounded for any p ∈ P1, and P1 is
a nonempty polytope.
