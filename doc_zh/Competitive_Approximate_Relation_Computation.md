# Computation of Approximate Probabilistic Relations under Competitive Interpretation

> **Note:** This document consolidates the competitive-semantics algorithm and its corner-based LP reduction, followed by a detailed analysis of why LP duality cannot eliminate the corner enumeration on the source-system side, and a survey of practical acceleration techniques.

---

## 1. Theoretical Foundation: Corner-Based Reduction

### 1.1 Theorem V.3 — Competitive Corner-Based Reduction

**Theorem V.3.** Given two IMDPs $\mathcal{M}_i = (X_i, x_0^i, A_i, \hat{P}_i, \check{P}_i, \mathcal{AP}_i, L_i)$, $i \in \{1,2\}$, and a relation $\mathcal{R} \subseteq X_1 \times X_2$. For any state pair $(x_1, x_2) \in \mathcal{R}$ and any action $a_2 \in A_2$, there exists an action $a_1 \in A_1$ such that for every distribution $\mu_1 \in \mathcal{P}(x_1, a_1)$, there exists a distribution $\mu_2 \in \mathcal{P}(x_2, a_2)$ with $(\mu_1, \mu_2) \in \overline{\mathcal{R}}_\varepsilon$, **if and only if**, there exists an action $a_1 \in A_1$ such that for every corner $c_1 \in \mathcal{C}(x_1, a_1)$, there exists a joint distribution $\mathcal{W}^{c_1}_\varepsilon \models \mathsf{Coupling}(x_1, a_1, x_2, a_2, c_1)$.

**Intuition.** The theorem reduces the competitive verification over the **infinite** set of feasible distributions $\mathcal{P}(x_1, a_1)$ to a **finite** check at the extreme points (corners) of the polytope $\mathcal{P}(x_1, a_1)$. The key difference from the cooperative case lies in the order of quantification: for every action $a_2 \in A_2$ of the abstract system, the concrete system must exhibit a defending action $a_1 \in A_1$ that robustly matches all corners $c_1 \in \mathcal{C}(x_1, a_1)$.

---

### 1.2 Corollary V.4 — Finite Characterization

**Corollary V.4.** Given two IMDPs $\mathcal{M}_i = (X_i, x_0^i, A_i, \hat{P}_i, \check{P}_i, \mathcal{AP}_i, L_i)$, $i \in \{1,2\}$, and a relation $\mathcal{R} \subseteq X_1 \times X_2$. $\mathcal{M}_2 \preceq_\varepsilon^{\forall\exists} \mathcal{M}_1$ under $\mathcal{R}$ if and only if:

1. $(x_0^1, x_0^2) \in \mathcal{R}$;
2. For all $(x_1, x_2) \in \mathcal{R}$, $L_1(x_1) = L_2(x_2)$;
3. For all $(x_1, x_2) \in \mathcal{R}$, all $a_2 \in A_2$, there exists an action $a_1 \in A_1$ such that for all corners $c_1 \in \mathcal{C}(x_1, a_1)$, there exists a joint distribution $\mathcal{W}^{c_1}_\varepsilon \in \mathsf{Dis}(X_1 \times X_2)$ satisfying $\mathcal{W}^{c_1}_\varepsilon \models \mathsf{Coupling}(x_1, a_1, x_2, a_2, c_1)$.

This corollary provides the explicit finite characterization suitable for algorithmic implementation.

---

### 1.3 Definition 5 — Coupling Constraint for Corners (Recalled)

**Definition 5 (Coupling Constraint for Corners).** Given two IMDPs $\mathcal{M}_i$, a relation $\mathcal{R} \subseteq X_1 \times X_2$, a state pair $(x_1, x_2) \in \mathcal{R}$, actions $a_1 \in A_1$, $a_2 \in A_2$, and a corner $c_1 \in \mathcal{C}(x_1, a_1)$. A joint probability distribution $\mathcal{W}^{c_1}_\varepsilon \in \mathsf{Dis}(X_1 \times X_2)$ satisfies the coupling constraint for $\varepsilon$ with respect to $c_1$, denoted by $\mathcal{W}^{c_1}_\varepsilon \models \mathsf{Coupling}(x_1, a_1, x_2, a_2, c_1)$, if there exists a vector $\beta^{c_1} \in [0,1]^{|\mathcal{C}(x_2, a_2)|}$ such that:

- **Marginal on $X_1$:** $\forall x_1' \in X_1, \sum_{x_2' \in X_2} \mathcal{W}^{c_1}_\varepsilon(x_1', x_2') = c_1(x_1')$;
- **Marginal on $X_2$:** $\forall x_2' \in X_2, \sum_{x_1' \in X_1} \mathcal{W}^{c_1}_\varepsilon(x_1', x_2') = \sum_{c_2^i \in \mathcal{C}(x_2, a_2)} \beta^{c_1}(i) \cdot c_2^i(x_2')$;
- **Relation mass:** $\sum_{(x_1', x_2') \in \mathcal{R}} \mathcal{W}^{c_1}_\varepsilon(x_1', x_2') \geq 1 - \varepsilon$;
- **Convex combination:** $\|\beta^{c_1}\|_1 = 1$.

---

## 2. Algorithm 2 — Computation of Competitive Approximate Relation

```text
Algorithm 2: Computation of competitive approximate relation
Input: two IMDPs M1, M2, threshold ε
Output: approximate probabilistic relation R
─────────────────────────────────────────────────────────────
 1  R ← {(x1, x2) : L1(x1) = L2(x2)};
 2  repeat
 3      R′ ← R;
 4      forall (x1, x2) ∈ R′ do
 5          valid ← True;
 6          forall a2 ∈ A2 s.t. valid do
 7              found ← False;
 8              forall a1 ∈ A1 s.t. ¬found do
 9                  ok ← True;
10                  forall c1 ∈ C(x1, a1) s.t. ok do
11                      feas ← Coupling(x1, a1, x2, a2, c1);
12                      if ¬feas then
13                          ok ← False;
14                  if ok then
15                      found ← True;
16              if ¬found then
17                  valid ← False;
18          if ¬valid then
19              R ← R \\ {(x1, x2)};
20  until R = R′;
21  return R;
```

### 2.1 Algorithm Walkthrough

The algorithm computes the **greatest fixed point** of the competitive approximate simulation relation via iterative partition refinement:

1. **Initialization (Line 1):** Start with all label-matching state pairs.
2. **Outer loop (Lines 2–20):** Repeat until the relation stabilizes (greatest fixed point).
3. **Universal quantification over abstract actions (Line 6):** For every action $a_2 \in A_2$ of the abstract system $\mathcal{M}_2$, the concrete system must be able to defend.
4. **Existential quantification over concrete actions (Line 8):** Search for a defending action $a_1 \in A_1$.
5. **Universal quantification over corners (Line 10):** For the candidate action $a_1$, verify that **all** corners $c_1 \in \mathcal{C}(x_1, a_1)$ can be matched.
6. **LP feasibility check (Line 11):** Each `Coupling` call is a linear programming feasibility problem with $O(|X_1||X_2|)$ variables and $O(|X_1| + |X_2|)$ constraints.
7. **Elimination (Line 19):** If any abstract action $a_2$ cannot be defended, remove the pair $(x_1, x_2)$ from $\mathcal{R}$.

---

### 2.2 Computational Complexity

The outer `repeat-until` loop executes at most $|X_1| \cdot |X_2|$ iterations, since $\mathcal{R}$ is monotone decreasing and finite. In each iteration, the algorithm inspects:

- Every pair $(x_1, x_2) \in \mathcal{R}'$,
- Every action $a_2 \in A_2$ of the abstract system,
- Every candidate action $a_1 \in A_1$ of the concrete system,
- Every corner $c_1 \in \mathcal{C}(x_1, a_1)$.

For each such quadruple, checking the `Coupling` constraint reduces to a linear program with $O(|X_1| \cdot |X_2|)$ variables and $O(|X_1| + |X_2|)$ constraints, solvable in polynomial time $\mathsf{LP}(n)$.

**Overall complexity:**

$$
\mathcal{O}\Bigl(|X_1|^2 |X_2|^2 \cdot |A_1| |A_2| \cdot \max_{x,a} |\mathcal{C}(x,a)| \cdot \mathsf{LP}(|X_1||X_2|)\Bigr)
$$

where $\mathsf{LP}(n)$ denotes the polynomial-time complexity of solving a linear program of size $n$. Thus, for bounded corner sets $\mathcal{C}(x,a)$, Algorithm 2 terminates in polynomial time in the size of the two IMDPs.

---

## 3. Why LP Duality Cannot Eliminate the Corner Enumeration

A natural question is whether LP duality can be exploited to avoid enumerating the corners $\mathcal{C}(x_1, a_1)$. The short answer is **no** — the corner enumeration on the source-system side ($\mathcal{P}(x_1, a_1)$) is not an artifact of the algorithmic formulation, but a **fundamental consequence** of the convex geometry of the problem. Below is the detailed reasoning.

---

### 3.1 The Core Problem is a Convex Inclusion Test

The competitive condition in Theorem V.3, for a fixed pair $(x_1, x_2) \in \mathcal{R}$ and a fixed action $a_2 \in A_2$, asks whether there exists $a_1 \in A_1$ such that:

$$
\forall \mu_1 \in \mathcal{P}(x_1, a_1), \quad \exists \mu_2 \in \mathcal{P}(x_2, a_2), \quad (\mu_1, \mu_2) \in \overline{\mathcal{R}}_\varepsilon.
$$

For a fixed $a_1$ and $a_2$, define the **feasible set** of source distributions that can be $\varepsilon$-lifted:

$$
\mathcal{S}_{a_2} := \Bigl\{ \mu_1 \in \mathsf{Dis}(X_1) \;\Big|\; \exists \mu_2 \in \mathcal{P}(x_2, a_2), \exists \mathcal{W} \in \mathsf{Dis}(X_1 \times X_2) \text{ s.t. } \mathcal{W} \models \mathsf{Coupling}(\mu_1, \mu_2, \mathcal{R}, \varepsilon) \Bigr\}.
$$

Here $\mathcal{W} \models \mathsf{Coupling}(\mu_1, \mu_2, \mathcal{R}, \varepsilon)$ means $\mathcal{W}$ has marginals $\mu_1, \mu_2$, and $\mathcal{W}(\mathcal{R}) \geq 1-\varepsilon$. The condition then becomes:

$$
\mathcal{P}(x_1, a_1) \;\subseteq\; \mathcal{S}_{a_2}.
\tag{1}
$$

**Key observation:** $\mathcal{S}_{a_2}$ is a **convex polytope**. This is because it is the projection of an LP feasible region (the coupling constraints) onto the $\mu_1$-coordinates. The constraints are linear in $\mathcal{W}$, and $\mu_1$ is a linear marginal of $\mathcal{W}$.

---

### 3.2 Minkowski-Weyl Theorem Makes Corner Checking Necessary

By the **Minkowski-Weyl theorem** [20], any convex polytope is the convex hull of its finitely many extreme points (corners). Specifically:

$$
\mathcal{P}(x_1, a_1) = \mathsf{conv}\bigl(\mathcal{C}(x_1, a_1)\bigr).
$$

Since $\mathcal{S}_{a_2}$ is convex, the inclusion (1) holds if and only if every generator of $\mathcal{P}(x_1, a_1)$ is contained in $\mathcal{S}_{a_2}$:

$$
\mathcal{P}(x_1, a_1) \subseteq \mathcal{S}_{a_2}
\quad\Longleftrightarrow\quad
\mathcal{C}(x_1, a_1) \subseteq \mathcal{S}_{a_2}.
\tag{2}
$$

**This equivalence is exact and irreversible.** It means that checking the universal quantifier $\forall \mu_1 \in \mathcal{P}(x_1, a_1)$ is **mathematically equivalent** to checking $\forall c_1 \in \mathcal{C}(x_1, a_1)$. No reformulation of the LP — primal, dual, or otherwise — can reduce the number of points that must be checked, because the convex hull structure is intrinsic to the geometry of $\mathcal{P}(x_1, a_1)$.

---

### 3.3 What LP Duality Actually Does (and Does Not Do)

LP duality can transform the **per-corner feasibility check** $c_1 \in \mathcal{S}_{a_2}$ into an alternative form. For a single corner $c_1$, the primal LP is:

$$
\begin{aligned}
\text{find} \quad & \mathcal{W}, \beta \\
\text{s.t.} \quad
& \sum_{x_2'} \mathcal{W}(x_1', x_2') = c_1(x_1'), \quad \forall x_1' \in X_1, \\
& \sum_{x_1'} \mathcal{W}(x_1', x_2') = \sum_i \beta_i \, c_{2,i}(x_2'), \quad \forall x_2' \in X_2, \\
& \sum_{(x_1',x_2') \in \mathcal{R}} \mathcal{W}(x_1', x_2') \geq 1-\varepsilon, \\
& \|\beta\|_1 = 1, \; \beta \geq 0, \; \mathcal{W} \geq 0.
\end{aligned}
$$

The dual LP provides a **certificate of infeasibility**: by Farkas' lemma, $c_1 \notin \mathcal{S}_{a_2}$ if and only if there exists a separating hyperplane (dual variable) that separates $c_1$ from $\mathcal{S}_{a_2}$. However, this duality operates **pointwise** — it replaces one LP with another LP for a **single** $c_1$. It does **not** provide a single dual program that simultaneously certifies $\mathcal{C}(x_1, a_1) \subseteq \mathcal{S}_{a_2}$ for all corners at once.

One might attempt to "dualize the universal quantifier" by aggregating all corners into a single meta-LP. For instance, one could try to write:

$$
\forall c_1 \in \mathcal{C}(x_1, a_1), \quad \exists \mathcal{W}, \beta \text{ s.t. } \text{Coupling constraints hold}.
$$

as a single optimization problem. However, the existential quantifier $\exists \mathcal{W}, \beta$ **depends** on $c_1$ (the coupling matrix must match the marginal $c_1$). This creates a **disjunction** over corners, or equivalently, a **bilinear** structure if one tries to share variables across corners. LP duality cannot linearize this disjunction without enumerating the corners.

---

### 3.4 The Farkas Alternative: Enumerating Dual Extremal Rays

A more sophisticated attempt is to apply Farkas' lemma to the inclusion (1) directly. The condition $\mathcal{P}(x_1, a_1) \subseteq \mathcal{S}_{a_2}$ can be written as:

$$
\forall \mu_1 \in \mathcal{P}(x_1, a_1), \; \forall y \in \mathcal{Y}, \quad y^\top B \mu_1 + y^\top b \geq 0,
$$

where $\mathcal{Y}$ is the cone of valid inequalities for $\mathcal{S}_{a_2}$ (derived from the dual LP). By Farkas' lemma, this is equivalent to checking the inequality on the **extremal rays** of $\mathcal{Y}$. 

**The catch:** the number of extremal rays of the dual cone can be **exponential** in the dimension of $\mu_1$, and in the worst case is as large as the number of vertices of $\mathcal{P}(x_1, a_1)$. Thus, enumerating dual extremal rays is computationally **equivalent** to enumerating primal corners. The complexity has not been reduced; it has merely been shifted from the primal space to the dual space.

---

### 3.5 Summary: The Fundamental Barrier

| Aspect | What LP Duality Can Do | What LP Duality Cannot Do |
|--------|------------------------|---------------------------|
| **Per-corner check** | Replace primal LP with dual LP (potentially better numerical stability) | Reduce the number of LPs to solve |
| **Corner enumeration** | Shift enumeration to dual cone extremal rays | Eliminate the enumeration entirely |
| **Source polytope** $\mathcal{P}(x_1, a_1)$ | Nothing — corners are geometric generators | Bypass Minkowski-Weyl theorem |
| **Target polytope** $\mathcal{P}(x_2, a_2)$ | **Yes** — see Section 4.1 | — |

**Conclusion:** The corner enumeration on $\mathcal{P}(x_1, a_1)$ is a **combinatorial bottleneck** rooted in the need to verify convex inclusion over a polytope. LP duality is a powerful tool for reformulating individual feasibility checks, but it cannot circumvent the fundamental geometric fact that a convex polytope is generated by its corners. Any exact algorithm must, in the worst case, inspect these generators.

---

## 4. Practical Improvements and Acceleration Techniques

While LP duality cannot eliminate the $\mathcal{C}(x_1, a_1)$ enumeration, several engineering and algorithmic improvements can significantly reduce the practical runtime.

---

### 4.1 Immediate Improvement: Direct Variableization of $\mathcal{P}(x_2, a_2)$

In Definition 5, the second marginal is explicitly represented as a convex combination of corners $\sum_i \beta_i c_{2,i}$. This introduces $|\mathcal{C}(x_2, a_2)|$ additional variables $\beta_i$ into the LP.

**Better formulation:** Treat $\mu_2$ directly as a variable and impose the interval bounds as linear constraints:

$$
\begin{aligned}
\text{find} \quad & \mathcal{W}, \mu_2 \\
\text{s.t.} \quad
& \sum_{x_2'} \mathcal{W}(x_1', x_2') = c_1(x_1'), \quad \forall x_1', \\
& \sum_{x_1'} \mathcal{W}(x_1', x_2') = \mu_2(x_2'), \quad \forall x_2', \\
& \check{P}_2(x_2, a_2, x_2') \leq \mu_2(x_2') \leq \hat{P}_2(x_2, a_2, x_2'), \quad \forall x_2', \\
& \sum_{x_2'} \mu_2(x_2') = 1, \quad \mu_2 \geq 0, \\
& \sum_{(x_1',x_2') \in \mathcal{R}} \mathcal{W}(x_1', x_2') \geq 1-\varepsilon, \quad \mathcal{W} \geq 0.
\end{aligned}
$$

**Benefit:** This removes the dependency on $|\mathcal{C}(x_2, a_2)|$ entirely. The LP size becomes $O(|X_1||X_2| + |X_2|)$ variables instead of $O(|X_1||X_2| + |\mathcal{C}(x_2, a_2)|)$. Since $|\mathcal{C}(x_2, a_2)|$ can be exponential in $|X_2|$ in the worst case, this is a **zero-cost, high-impact** improvement.

---

### 4.2 Lazy Corner Enumeration (Cutting-Plane / Column Generation)

Instead of pre-computing all corners of $\mathcal{P}(x_1, a_1)$, generate them **on demand**:

1. Start with a small subset $\mathcal{C}_0 \subseteq \mathcal{C}(x_1, a_1)$ (e.g., a few randomly sampled corners or the most "extreme" ones).
2. For the current candidate action $a_1$, solve the LP for all $c_1 \in \mathcal{C}_0$.
3. If all pass, solve a **separation subproblem**: find the corner $c_1^* \in \mathcal{C}(x_1, a_1)$ that maximally violates the coupling condition (or prove that no such corner exists).
4. If $c_1^*$ exists, add it to $\mathcal{C}_0$ and repeat; otherwise, the action $a_1$ is valid.

**How to find the most violated corner?** The separation problem can be formulated as an LP over $\mathcal{P}(x_1, a_1)$ with a linear objective derived from the dual variables of the coupling LP. Because $\mathcal{P}(x_1, a_1)$ is a box-constrained simplex, this separation LP is tractable.

**Benefit:** In practice, only a tiny fraction of corners are "active" (tight) for the inclusion test. Lazy enumeration avoids generating the full exponential set upfront.

---

### 4.3 Exploiting Interval-Polytope Structure

The feasible set $\mathcal{P}(x, a)$ for an IMDP is not an arbitrary polytope — it is the intersection of the probability simplex with **box constraints** (interval bounds):

$$
\mathcal{P}(x, a) = \Bigl\{ p \in \mathbb{R}^{|X|} \;\Big|\; \sum_{x'} p(x') = 1, \; \check{P}(x,a,x') \leq p(x') \leq \hat{P}(x,a,x') \Bigr\}.
$$

This structure implies that the corners have a very specific form: **at most one coordinate is strictly inside its interval, while all others are at their lower or upper bounds**. This is because the simplex constraint $\sum p = 1$ is the only equality; the rest are independent bound constraints.

**Algorithmic consequence:** One can enumerate corners by:
1. Fixing all but one coordinate to either $\check{P}$ or $\hat{P}$.
2. Checking whether the remaining coordinate can be set to satisfy $\sum p = 1$ while staying within its interval.

This reduces the naive enumeration from $2^{|X|}$ to $O(|X| \cdot 2^{|X|-1})$ in the worst case, but more importantly, it enables **lexicographic generation** and **early termination** — if a partial assignment already violates the simplex sum bounds, the entire branch can be pruned.

---

### 4.4 Multi-Parametric LP Precomputation

For a fixed $(x_1, x_2)$ and $a_2$, the set $\mathcal{S}_{a_2}$ is fixed. Instead of solving a fresh LP for each corner $c_1$, one can precompute the **explicit polytopic partition** of $\mathcal{S}_{a_2}$ using multi-parametric LP (mp-LP), where $c_1$ is treated as a parameter vector.

The mp-LP solver partitions the parameter space (the space of possible $c_1$) into **critical regions**, each associated with a fixed active constraint set. Within each region, the feasibility of $c_1 \in \mathcal{S}_{a_2}$ can be tested by simple linear inequalities (no LP solver needed).

**Benefit:** After the one-time mp-LP overhead, each corner check becomes a constant-time region lookup. This is especially effective when the same $(x_1, x_2, a_2)$ triple is reused across multiple iterations of Algorithm 2 (which happens frequently as $\mathcal{R}$ shrinks).

---

### 4.5 Benders Decomposition

The nested loop structure of Algorithm 2 (corners inside actions inside state pairs) has a natural two-stage structure amenable to **Benders decomposition**:

- **Master problem:** Select the defending action $a_1 \in A_1$.
- **Subproblem:** For each corner $c_1 \in \mathcal{C}(x_1, a_1)$, check coupling feasibility.

If a subproblem is infeasible for some $c_1$, a **Benders cut** is added to the master problem, eliminating the current $a_1$ (or a subset of $a_1$ choices) without explicitly checking all remaining corners for that $a_1$.

**Benefit:** Benders cuts accumulate across iterations of Algorithm 2, progressively narrowing the search space for $a_1$. In practice, many actions are ruled out by cuts after only a few corner checks.

---

### 4.6 GPU Batch Solving

Modern LP solvers (e.g., cuSOLVER, Gurobi's GPU capabilities) can solve batches of LPs in parallel. Since the innermost loop of Algorithm 2 (Line 10–13) performs independent feasibility checks for each corner $c_1$, these can be batched and offloaded to a GPU.

**Benefit:** While this does not reduce the theoretical complexity, it can provide a **10–100× speedup** in practice when $|\mathcal{C}(x_1, a_1)|$ is large and the LP size is moderate.

---

## 5. Recommendations for Paper Writing

1. **Keep the corner-based theoretical formulation** in the main theorem (Theorem V.3 / Corollary V.4). The Minkowski-Weyl reduction is standard, elegant, and theoretically complete.

2. **Add an implementation remark** in the computation section stating that in the actual LP, $\mu_2$ is treated as a direct variable with interval constraints, avoiding the explicit enumeration of $\mathcal{C}(x_2, a_2)$. This is a clean separation between theory (corners) and practice (LP variables).

3. **If space permits**, briefly mention lazy corner enumeration or interval-polytope pruning as future implementation optimizations. This signals to reviewers that you are aware of the practical scalability issues and have a roadmap to address them.

4. **Do not claim that LP duality eliminates corner enumeration** — this is a common misconception that sharp reviewers will catch. Instead, explicitly state that the corner check is a geometric necessity due to the convex-hull structure of $\mathcal{P}(x_1, a_1)$.

---

## 6. References (from the Draft)

- [20] R. Rockafellar. *Convex Analysis*, volume 28. Princeton University Press, 1997. (Minkowski-Weyl theorem)
- [15] V. Hashemi et al. Polynomial-time alternating probabilistic bisimulation for interval MDPs. *SETTA*, 2017.
- [16] V. Hashemi et al. Probabilistic bisimulations for PCTL model checking of interval MDPs. *arXiv:1403.2864*, 2014.
