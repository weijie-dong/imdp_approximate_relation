# IMDP Running Examples — Reproduction Document (Corrected Parameters)

> **Note**: The transition probability intervals for Fig. 3 and Fig. 4 in this document are based on the user's latest corrections. All feasible sets, corners, and coupling constructions are re-derived analytically based on the corrected parameters. If there are discrepancies with the original paper text, the values in this document shall prevail.

---

## 1. Model Definition

### 1.1 IMDP $\mathcal{M}_1$ (Fig. 3)

- **State set**: $X_1 = \{p_1, q_1, r_1\}$
- **Initial state**: $x_0^1 = p_1$
- **Action set**: $A_1 = \{\alpha, \beta\}$
- **Atomic propositions**: $\mathcal{AP}_1 = \{G, U\}$
- **Labeling function**:
  - $L_1(p_1) = \emptyset$
  - $L_1(q_1) = \{G\}$
  - $L_1(r_1) = \{U\}$

**Transition probability intervals**:

| Current state | Action | Successor state | Lower bound $\check{P}_1$ | Upper bound $\hat{P}_1$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_1$ | $\alpha$ | $q_1$ | 0.1 | 0.6 |
| $p_1$ | $\alpha$ | $r_1$ | 0.0 | 1.0 |
| $p_1$ | $\beta$ | $q_1$ | 0.0 | 0.6 |
| $p_1$ | $\beta$ | $r_1$ | 0.0 | 1.0 |
| $q_1$ | $\alpha$ | $q_1$ | 1.0 | 1.0 |
| $r_1$ | $\beta$ | $r_1$ | 1.0 | 1.0 |

---

### 1.2 IMDP $\mathcal{M}_2$ (Fig. 4)

- **State set**: $X_2 = \{p_2, q_2, r_2\}$
- **Initial state**: $x_0^2 = p_2$
- **Action set**: $A_2 = \{\gamma, \delta\}$
- **Atomic propositions**: $\mathcal{AP}_2 = \{G, U\}$
- **Labeling function**:
  - $L_2(p_2) = \emptyset$
  - $L_2(q_2) = \{G\}$
  - $L_2(r_2) = \{U\}$

**Transition probability intervals** (where $t \geq 0$ is a tunable parameter, corresponding to the value of $\varepsilon$ in approximate simulation):

| Current state | Action | Successor state | Lower bound $\check{P}_2$ | Upper bound $\hat{P}_2$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_2$ | $\gamma$ | $q_2$ | 0.1 | $0.6+t$ |
| $p_2$ | $\gamma$ | $r_2$ | 0.0 | 1.0 |
| $p_2$ | $\delta$ | $q_2$ | 0.1 | 0.8 |
| $p_2$ | $\delta$ | $r_2$ | 0.0 | 1.0 |
| $q_2$ | $\gamma$ | $q_2$ | 1.0 | 1.0 |
| $r_2$ | $\delta$ | $r_2$ | 1.0 | 1.0 |

---

## 2. Analytical Derivation of Feasible Sets

By combining interval constraints with the probability normalization condition $\sum_{x'} p(x') = 1$, we obtain the feasible set and its corners (extreme points) for each state-action pair.

### 2.1 $\mathcal{M}_1$

#### $\mathcal{P}_1(p_1, \alpha)$

Constraints:
- $0.1 \leq p(q_1) \leq 0.6$
- $0.0 \leq p(r_1) \leq 1.0$
- $p(q_1) + p(r_1) = 1$

From normalization, $p(r_1) = 1 - p(q_1) \in [0.4, 0.9]$. Intersecting with $p(r_1) \in [0.0, 1.0]$ gives $p(r_1) \in [0.4, 0.9]$, corresponding to $p(q_1) \in [0.1, 0.6]$.

- **Feasible set**:
  $$\mathcal{P}_1(p_1,\alpha) = \{(p,\, 1-p) \mid p \in [0.1, 0.6]\}$$
- **Corners**:
  - $c_{1,\alpha}^{(1)} = (0.1,\, 0.9)$  (i.e., $q_1$ probability 0.1, $r_1$ probability 0.9)
  - $c_{1,\alpha}^{(2)} = (0.6,\, 0.4)$

#### $\mathcal{P}_1(p_1, \beta)$

Constraints:
- $0.0 \leq p(q_1) \leq 0.6$
- $0.0 \leq p(r_1) \leq 1.0$
- $p(q_1) + p(r_1) = 1$

From normalization, $p(r_1) = 1 - p(q_1) \in [0.4, 1.0]$. Intersecting with the upper bound $1.0$ still yields $[0.4, 1.0]$, corresponding to $p(q_1) \in [0.0, 0.6]$.

- **Feasible set**:
  $$\mathcal{P}_1(p_1,\beta) = \{(p,\, 1-p) \mid p \in [0.0, 0.6]\}$$
- **Corners**:
  - $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$
  - $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$

#### $\mathcal{P}_1(q_1, \alpha)$ and $\mathcal{P}_1(r_1, \beta)$

Both are self-loop point distributions:
- $\mathcal{P}_1(q_1,\alpha) = \{(1.0,\, 0.0)\}$
- $\mathcal{P}_1(r_1,\beta) = \{(0.0,\, 1.0)\}$

---

### 2.2 $\mathcal{M}_2$

#### $\mathcal{P}_2(p_2, \gamma)$ (parameter $t$)

Constraints:
- $0.1 \leq p(q_2) \leq 0.6+t$
- $0.0 \leq p(r_2) \leq 1.0$
- $p(q_2) + p(r_2) = 1$

From normalization, $p(r_2) = 1 - p(q_2)$, and $p(q_2) \leq 1$ (since $p(r_2) \geq 0$). Thus the actual $p(q_2) \in [0.1,\, \min(0.6+t,\, 1)]$, $p(r_2) \in [1-\min(0.6+t,1),\, 0.9]$.

- **When $t=0$ (i.e., $\varepsilon=0$)**:
  $$\mathcal{P}_2(p_2,\gamma) = \{(q,\, 1-q) \mid q \in [0.1, 0.6]\}$$
  Corners: $c_{2,\gamma}^{(1)} = (0.1,\, 0.9)$, $c_{2,\gamma}^{(2)} = (0.6,\, 0.4)$

- **When $t=0.5$ (i.e., $\varepsilon=0.5$)**:
  The upper bound $0.6+0.5=1.1$ is truncated to $1.0$ by the normalization constraint,
  $$\mathcal{P}_2(p_2,\gamma) = \{(q,\, 1-q) \mid q \in [0.1, 1.0]\}$$
  Corners: $c_{2,\gamma}^{(1)} = (0.1,\, 0.9)$, $c_{2,\gamma}^{(2)} = (1.0,\, 0.0)$

#### $\mathcal{P}_2(p_2, \delta)$

Constraints:
- $0.1 \leq p(q_2) \leq 0.8$
- $0.0 \leq p(r_2) \leq 1.0$
- $p(q_2) + p(r_2) = 1$

From normalization, $p(r_2) = 1 - p(q_2) \in [0.2, 0.9]$. Intersecting with $[0.0, 1.0]$ still yields $[0.2, 0.9]$.

- **Feasible set**:
  $$\mathcal{P}_2(p_2,\delta) = \{(q,\, 1-q) \mid q \in [0.1, 0.8]\}$$
- **Corners**:
  - $c_{2,\delta}^{(1)} = (0.1,\, 0.9)$
  - $c_{2,\delta}^{(2)} = (0.8,\, 0.2)$

#### $\mathcal{P}_2(q_2, \gamma)$ and $\mathcal{P}_2(r_2, \delta)$

- $\mathcal{P}_2(q_2,\gamma) = \{(1.0,\, 0.0)\}$
- $\mathcal{P}_2(r_2,\delta) = \{(0.0,\, 1.0)\}$

---

## 3. Running Example 1: Approximate Simulation Relation Verification

**Candidate relation**:
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

### 3.1 Cooperative Semantics ($\mathcal{M}_2 \preceq_\varepsilon^\forall \mathcal{M}_1$), $\varepsilon = 0$

Verification condition: For every $(x_1,x_2) \in \mathcal{R}$, every $a_1 \in A_1$, every $\mu_1 \in \mathcal{P}_1(x_1,a_1)$, there exist $a_2 \in A_2$ and $\mu_2 \in \mathcal{P}_2(x_2,a_2)$ such that there exists a coupling $\mathcal{W}$ satisfying $\mathcal{W}(\mathcal{R}) \geq 1$ (i.e., exact matching).

#### Check $(p_1, p_2)$, action $a_1 = \alpha$

- $\mu_1 \in \mathcal{P}_1(p_1,\alpha)$, feasible set is $q_1 \in [0.1, 0.6]$.
- Choose abstract action $a_2 = \gamma$ ($t=0$), where $\mathcal{P}_2(p_2,\gamma)$ coincides exactly with $\mathcal{P}_1(p_1,\alpha)$.
- For any $\mu_1 = (p,\, 1-p)$, take $\mu_2 = \mu_1 = (p,\, 1-p) \in \mathcal{P}_2(p_2,\gamma)$.
- Coupling construction: $\mathcal{W}(q_1,q_2) = p$, $\mathcal{W}(r_1,r_2) = 1-p$, others 0.
- $\mathcal{W}(\mathcal{R}) = 1 \geq 1$. **Satisfied**.

#### Check $(p_1, p_2)$, action $a_1 = \beta$

- $\mathcal{P}_1(p_1,\beta)$ contains corner $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$ (i.e., $q_1$ probability 0, $r_1$ probability 1).
- For any $a_2 \in A_2$:
  - If $a_2 = \gamma$ ($t=0$): $\mathcal{P}_2(p_2,\gamma)$ requires $q_2 \geq 0.1$, so there is no $\mu_2$ with $\mu_2(q_2) = 0$. Any coupling must place mass 1 on the $r_1$ row, but $r_1$ can only be related to $r_2$ (since $(r_1,q_2) \notin \mathcal{R}$), and $\mu_2(r_2) = 1 - \mu_2(q_2) \leq 0.9 < 1$, so exact matching is impossible.
  - If $a_2 = \delta$: Similarly, $\mathcal{P}_2(p_2,\delta)$ requires $q_2 \geq 0.1$, unable to exactly match $\mu_1 = (0,1)$.
- **Conclusion**: Corner $(0.0, 1.0)$ cannot be exactly matched by any $a_2$, so $(p_1,p_2)$ **does not satisfy** the cooperative $\varepsilon=0$ condition.

#### Conclusion (Cooperative $\varepsilon=0$)

The maximum cooperative exact simulation relation is:
$$\mathcal{R} = \{(q_1,q_2),\, (r_1,r_2)\}$$
($(p_1,p_2)$ is removed)

---

### 3.2 Competitive Semantics ($\mathcal{M}_2 \preceq_\varepsilon^{\forall\exists} \mathcal{M}_1$), $\varepsilon = 0$

Verification condition: For every $(x_1,x_2) \in \mathcal{R}$, every $a_2 \in A_2$, there exists $a_1 \in A_1$ such that for every $\mu_1 \in \mathcal{P}_1(x_1,a_1)$, there exists $\mu_2 \in \mathcal{P}_2(x_2,a_2)$ that exactly matches.

#### Check $(p_1, p_2)$, $a_2 = \gamma$ ($t=0$)

- Try $a_1 = \alpha$:
  - $\mathcal{P}_1(p_1,\alpha)$ corners are $(0.1,0.9)$ and $(0.6,0.4)$.
  - For $\mu_1 = (0.1,0.9)$: Take $\mu_2 = (0.1,0.9) \in \mathcal{P}_2(p_2,\gamma)$, coupling $\mathcal{W}(q_1,q_2)=0.1$, $\mathcal{W}(r_1,r_2)=0.9$, $\mathcal{W}(\mathcal{R})=1$.
  - For $\mu_1 = (0.6,0.4)$: Take $\mu_2 = (0.6,0.4) \in \mathcal{P}_2(p_2,\gamma)$, similarly $\mathcal{W}(\mathcal{R})=1$.
  - By convexity, all intermediate distributions can be exactly matched.
- **Conclusion**: $a_1 = \alpha$ successfully defends against $a_2 = \gamma$.

#### Check $(p_1, p_2)$, $a_2 = \delta$

- Try $a_1 = \alpha$:
  - $\mathcal{P}_1(p_1,\alpha) \subseteq \mathcal{P}_2(p_2,\delta)$?
    - $\mathcal{P}_1(p_1,\alpha)$: $q_1 \in [0.1, 0.6]$.
    - $\mathcal{P}_2(p_2,\delta)$: $q_2 \in [0.1, 0.8]$.
    - Clearly $[0.1, 0.6] \subseteq [0.1, 0.8]$, and after normalization $r_1 = 1-q_1$ automatically satisfies the $r_2$ interval.
  - Thus for any $\mu_1 \in \mathcal{P}_1(p_1,\alpha)$, taking $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\delta)$ gives exact matching.
- **Conclusion**: $a_1 = \alpha$ successfully defends against $a_2 = \delta$.

#### Conclusion (Competitive $\varepsilon=0$)

$(p_1,p_2)$ satisfies the competitive exact simulation condition. Combined with the trivial self-loops of $(q_1,q_2)$ and $(r_1,r_2)$, the maximum relation is:
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

### 3.3 Competitive Semantics, $\varepsilon = 0.5$ ($t=0.5$)

Now $\mathcal{P}_2(p_2,\gamma)$ expands to $q_2 \in [0.1, 1.0]$.

#### Check $(p_1, p_2)$, $a_2 = \gamma$

- Try $a_1 = \alpha$:
  - $\mu_1 = (0.1, 0.9)$: Take $\mu_2 = (0.1, 0.9) \in \mathcal{P}_2(p_2,\gamma)$ (since $q_2=0.1$ is the lower bound, $r_2=0.9 \in [0,0.9]$). $\mathcal{W}(\mathcal{R}) = 1 \geq 0.5$.
  - $\mu_1 = (0.6, 0.4)$: Take $\mu_2 = (0.6, 0.4) \in \mathcal{P}_2(p_2,\gamma)$ (since $q_2=0.6 \leq 1.0$, $r_2=0.4 \geq 0$). $\mathcal{W}(\mathcal{R}) = 1 \geq 0.5$.
- **Conclusion**: $a_1 = \alpha$ defends against $a_2 = \gamma$.

#### Check $(p_1, p_2)$, $a_2 = \delta$

- Try $a_1 = \beta$:
  - $\mu_1 = (0.0, 1.0)$ (corner):
    - Need to construct $\mu_2 \in \mathcal{P}_2(p_2,\delta)$ such that coupling $\mathcal{W}(\mathcal{R}) \geq 0.5$.
    - Since $\mu_1(q_1)=0$, in the coupling $\mathcal{W}(q_1,\cdot)=0$, so $\mathcal{W}(\mathcal{R}) = \mathcal{W}(r_1,r_2) = \mu_2(r_2)$.
    - Need $\mu_2(r_2) \geq 0.5$, i.e., $\mu_2(q_2) \leq 0.5$.
    - $\mathcal{P}_2(p_2,\delta)$ allows $q_2 \in [0.1, 0.8]$, take $\mu_2 = (0.2,\, 0.8)$.
    - Coupling: $\mathcal{W}(r_1,q_2)=0.2$, $\mathcal{W}(r_1,r_2)=0.8$, $\mathcal{W}(\mathcal{R}) = 0.8 \geq 0.5$.
  - $\mu_1 = (0.6, 0.4)$ (corner):
    - Take $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\delta)$ ($q_2=0.6 \in [0.1,0.8]$, $r_2=0.4 \in [0.2,0.9]$).
    - Coupling: $\mathcal{W}(q_1,q_2)=0.6$, $\mathcal{W}(r_1,r_2)=0.4$, $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$.
  - By convexity, all intermediate distributions can be matched.
- **Conclusion**: $a_1 = \beta$ defends against $a_2 = \delta$.

#### Conclusion (Competitive $\varepsilon=0.5$)

$$\mathcal{M}_2 \preceq_{0.5}^{\forall\exists} \mathcal{M}_1$$
The maximum relation is still $\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$.

---

## 4. Running Example 2: Algorithm 1 (Cooperative, $\varepsilon = 0.2$)

**Setting**: $t = 0.2$ (corresponding to $\varepsilon=0.2$), then
- $\mathcal{P}_2(p_2,\gamma) = \{(q,1-q) \mid q \in [0.1, 0.8]\}$ (upper bound $0.6+0.2=0.8$)
- $\mathcal{P}_2(p_2,\delta) = \{(q,1-q) \mid q \in [0.1, 0.8]\}$ (coincidentally the same as $\gamma$)

**Initialization**:
$$\mathcal{R} \leftarrow \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

### Iteration 1

Check $(p_1, p_2)$:

**(a) $a_1 = \alpha$, corners of $\mathcal{P}_1(p_1,\alpha)$:**

- Corner $c_{1,\alpha}^{(1)} = (0.1,\, 0.9)$:
  - Try $a_2 = \gamma$: Take $\mu_2 = (0.1,\, 0.9) \in \mathcal{P}_2(p_2,\gamma)$.
  - Coupling: $\mathcal{W}(q_1,q_2)=0.1$, $\mathcal{W}(r_1,r_2)=0.9$.
  - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$. **Feasible**.

- Corner $c_{1,\alpha}^{(2)} = (0.6,\, 0.4)$:
  - Try $a_2 = \gamma$: Take $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\gamma)$.
  - Coupling: $\mathcal{W}(q_1,q_2)=0.6$, $\mathcal{W}(r_1,r_2)=0.4$.
  - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$. **Feasible**.

**(b) $a_1 = \beta$, corners of $\mathcal{P}_1(p_1,\beta)$:**

- Corner $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$:
  - Try $a_2 = \delta$: Need $\mathcal{W}(\mathcal{R}) \geq 0.8$.
  - Since $\mu_1(q_1)=0$, $\mathcal{W}(\mathcal{R}) = \mu_2(r_2)$, need $\mu_2(r_2) \geq 0.8$ (i.e., $\mu_2(q_2) \leq 0.2$).
  - $\mathcal{P}_2(p_2,\delta)$ allows $q_2 \in [0.1, 0.8]$, take $\mu_2 = (0.2,\, 0.8)$.
  - Coupling: $\mathcal{W}(r_1,q_2)=0.2$, $\mathcal{W}(r_1,r_2)=0.8$.
  - $\mathcal{W}(\mathcal{R}) = 0.8 \geq 0.8$. **Feasible**.

- Corner $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$:
  - Try $a_2 = \delta$: Take $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\delta)$.
  - Coupling: $\mathcal{W}(q_1,q_2)=0.6$, $\mathcal{W}(r_1,r_2)=0.4$.
  - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$. **Feasible**.

Check $(q_1, q_2)$ and $(r_1, r_2)$: Self-loops, trivial, retained.

**Removed this round**: None.

### Iteration 2
$\mathcal{R}$ unchanged, algorithm terminates.

**Output**:
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

## 5. Running Example 3: Algorithm 2 (Competitive, $\varepsilon = 0.5$)

**Setting**: $t = 0.5$, then
- $\mathcal{P}_2(p_2,\gamma) = \{(q,1-q) \mid q \in [0.1, 1.0]\}$
- $\mathcal{P}_2(p_2,\delta) = \{(q,1-q) \mid q \in [0.1, 0.8]\}$

**Initialization**:
$$\mathcal{R} \leftarrow \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

### Iteration 1

Check $(p_1, p_2)$:

**(a) $a_2 = \gamma$:**

- Try $a_1 = \alpha$:
  - Corner $c_{1,\alpha}^{(1)} = (0.1,\, 0.9)$:
    - Take $\mu_2 = (0.1,\, 0.9) \in \mathcal{P}_2(p_2,\gamma)$.
    - Coupling: $\mathcal{W}(q_1,q_2)=0.1$, $\mathcal{W}(r_1,r_2)=0.9$.
    - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$. **Feasible**.
  - Corner $c_{1,\alpha}^{(2)} = (0.6,\, 0.4)$:
    - Take $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\gamma)$.
    - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$. **Feasible**.
  - All corners feasible, set $found \leftarrow \text{True}$.

**(b) $a_2 = \delta$:**

- Try $a_1 = \beta$:
  - Corner $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$:
    - Need $\mathcal{W}(\mathcal{R}) \geq 0.5$. Since $\mu_1(q_1)=0$, $\mathcal{W}(\mathcal{R}) = \mu_2(r_2)$.
    - Take $\mu_2 = (0.2,\, 0.8) \in \mathcal{P}_2(p_2,\delta)$, then $\mathcal{W}(\mathcal{R}) = 0.8 \geq 0.5$. **Feasible**.
  - Corner $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$:
    - Take $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\delta)$.
    - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$. **Feasible**.
  - All corners feasible, set $found \leftarrow \text{True}$.

Check $(q_1, q_2)$, $(r_1, r_2)$: Self-loops, trivial.

**Removed this round**: None.

### Iteration 2
$\mathcal{R}$ unchanged, algorithm terminates.

**Output**:
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

## 6. Program Reproduction Tips

### 6.1 Data Structure Definition

```python
# M1
X1 = ['p1', 'q1', 'r1']
A1 = ['alpha', 'beta']
x0_1 = 'p1'
# P1_lower[x][a][x_next], P1_upper[x][a][x_next]
# Example: P1_lower['p1']['alpha']['q1'] = 0.1

# M2
X2 = ['p2', 'q2', 'r2']
A2 = ['gamma', 'delta']
x0_2 = 'p2'

# Candidate relation
R = {('p1','p2'), ('q1','q2'), ('r1','r2')}
```

### 6.2 Generating Feasible Set Corners

For each $(x,a)$, derive the explicit feasible interval for each successor state probability from interval and normalization constraints, then take the extreme points. For cases with only two successor states (e.g., the actions of $p_1$), parameterize directly as $p(q)=t$, $p(r)=1-t$, find the closed interval for $t$, whose endpoints are the corners.

### 6.3 Coupling LP (Definition 6)

For a given corner $c_1 \in C(x_1,a_1)$, action $a_2$, and threshold $\varepsilon$:

**Variables**:
- $\mathcal{W}(x_1', x_2')$ for all $(x_1', x_2') \in X_1 \times X_2$
- $\beta_i$ for each corner $c_2^i \in C(x_2, a_2)$

**Constraints**:
1. $\forall x_1' \in X_1: \sum_{x_2'} \mathcal{W}(x_1', x_2') = c_1(x_1')$
2. $\forall x_2' \in X_2: \sum_{x_1'} \mathcal{W}(x_1', x_2') = \sum_{i} \beta_i \cdot c_2^i(x_2')$
3. $\sum_{(x_1',x_2') \in \mathcal{R}} \mathcal{W}(x_1', x_2') \geq 1 - \varepsilon$
4. $\sum_{i} \beta_i = 1,\; \beta_i \geq 0$
5. $\mathcal{W} \geq 0$

### 6.4 Key Verification Points

When reproducing in code, prioritize verifying the following manually derived conclusions:

1. **Cooperative $\varepsilon=0$**: $(p_1,p_2)$ should be removed, because the corner $(0,1)$ of $a_1=\beta$ cannot be exactly matched by any $a_2$.
2. **Competitive $\varepsilon=0$**: $(p_1,p_2)$ should be retained, because $a_2=\gamma$ can be exactly defended by $a_1=\alpha$, and $a_2=\delta$ can also be exactly defended by $a_1=\alpha$.
3. **Algorithm 1 ($\varepsilon=0.2$)**: $(p_1,p_2)$ retained. For the corner $(0,1)$ of $a_1=\beta$ vs $a_2=\delta$, taking $\mu_2=(0.2,0.8)$ exactly yields $\mathcal{W}(\mathcal{R})=0.8$.
4. **Algorithm 2 ($\varepsilon=0.5$)**: $(p_1,p_2)$ retained. When $a_2=\delta$ is defended by $a_1=\beta$, corner $(0,1)$ with $\mu_2=(0.2,0.8)$ yields $\mathcal{W}(\mathcal{R})=0.8 \geq 0.5$.

## Appendix: Explicit Coupling LP Example

Take Example 2, $(p_1,\beta)$ vs $(p_2,\delta)$, corner $c_1=(0,1)$, $\varepsilon=0.2$:

**Given**:
- $c_1(q_1)=0,\; c_1(r_1)=1$
- $C(p_2,\delta) = \{(0.1,0.9),\, (0.8,0.2)\}$

**Variables**: $\mathcal{W}_{qq}, \mathcal{W}_{qr}, \mathcal{W}_{rq}, \mathcal{W}_{rr}, \beta_1, \beta_2$

**Constraints**:

```text
# M1 marginal
W_qq + W_qr = 0
W_rq + W_rr = 1

# M2 marginal (convex combination)
W_qq + W_rq = 0.1*beta_1 + 0.8*beta_2
W_qr + W_rr = 0.9*beta_1 + 0.2*beta_2

# Relation mass
W_qq + W_rr >= 0.8

# Convex combination
beta_1 + beta_2 = 1
beta_1, beta_2 >= 0

# Non-negativity
W_qq, W_qr, W_rq, W_rr >= 0
```

**Feasible solution**: Take $\beta_1=1, \beta_2=0$ (i.e., $\mu_2=(0.1,0.9)$), then
- $\mathcal{W}_{rq}=0.1,\; \mathcal{W}_{rr}=0.9$, others 0.
- $\mathcal{W}(\mathcal{R})=0.9 \geq 0.8$.

Or take $\mu_2=(0.2,0.8)$ (not a corner, but can be obtained as a convex combination of corners), then
- $\mathcal{W}_{rq}=0.2,\; \mathcal{W}_{rr}=0.8$.
- $\mathcal{W}(\mathcal{R})=0.8 \geq 0.8$.
