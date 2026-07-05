# IMDP Approximate Bisimulation Case Study — Manual Derivation & Program Reproduction

> **Case Design Intent**: The parameters of both IMDP models in this case are **fixed intervals** that do not change with $\varepsilon$. The approximate relation emerges not from "modifying the model" but naturally through **coupling relaxation**. The case clearly demonstrates:
> - Under Cooperative semantics, $\varepsilon=0$ holds exactly;
> - Under Competitive semantics, $\varepsilon=0$ does NOT hold exactly, but $\varepsilon=0.2$ holds approximately;
> - The same state pair $(p_1,p_2)$ exhibits distinctly different behavior under different semantics, highlighting the key role of the Interface block in choosing actions.

---

## 1. Model Definition

### 1.1 IMDP $\mathcal{M}_1$ (Concrete)

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
| $p_1$ | $\alpha$ | $q_1$ | 0.2 | 0.7 |
| $p_1$ | $\alpha$ | $r_1$ | 0.1 | 0.6 |
| $p_1$ | $\beta$ | $q_1$ | 0.1 | 0.6 |
| $p_1$ | $\beta$ | $r_1$ | 0.2 | 0.8 |
| $q_1$ | $\alpha$ | $q_1$ | 1.0 | 1.0 |
| $r_1$ | $\beta$ | $r_1$ | 1.0 | 1.0 |

---

### 1.2 IMDP $\mathcal{M}_2$ (Abstract)

- **State set**: $X_2 = \{p_2, q_2, r_2\}$
- **Initial state**: $x_0^2 = p_2$
- **Action set**: $A_2 = \{\gamma, \delta\}$
- **Atomic propositions**: $\mathcal{AP}_2 = \{G, U\}$
- **Labeling function**:
  - $L_2(p_2) = \emptyset$
  - $L_2(q_2) = \{G\}$
  - $L_2(r_2) = \{U\}$

**Transition probability intervals**:

| Current state | Action | Successor state | Lower bound $\check{P}_2$ | Upper bound $\hat{P}_2$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_2$ | $\gamma$ | $q_2$ | 0.1 | 0.8 |
| $p_2$ | $\gamma$ | $r_2$ | 0.1 | 0.8 |
| $p_2$ | $\delta$ | $q_2$ | 0.1 | 0.4 |
| $p_2$ | $\delta$ | $r_2$ | 0.4 | 0.8 |
| $q_2$ | $\gamma$ | $q_2$ | 1.0 | 1.0 |
| $r_2$ | $\delta$ | $r_2$ | 1.0 | 1.0 |

---

## 2. Analytical Derivation of Feasible Sets

### 2.1 $\mathcal{M}_1$

#### $\mathcal{P}_1(p_1, \alpha)$

Let $p(q_1) = t$, then $p(r_1) = 1-t$. Constraints:
- $0.2 \leq t \leq 0.7$
- $0.1 \leq 1-t \leq 0.6 \;\Rightarrow\; 0.4 \leq t \leq 0.9$

Intersection gives $t \in [0.4, 0.7]$.

- **Feasible set**:
  $$\mathcal{P}_1(p_1,\alpha) = \{(t,\, 1-t) \mid t \in [0.4, 0.7]\}$$
- **Corners**:
  - $c_{1,\alpha}^{(1)} = (0.4,\, 0.6)$
  - $c_{1,\alpha}^{(2)} = (0.7,\, 0.3)$

#### $\mathcal{P}_1(p_1, \beta)$

Let $p(q_1) = t$. Constraints:
- $0.1 \leq t \leq 0.6$
- $0.2 \leq 1-t \leq 0.8 \;\Rightarrow\; 0.2 \leq t \leq 0.8$

Intersection gives $t \in [0.2, 0.6]$.

- **Feasible set**:
  $$\mathcal{P}_1(p_1,\beta) = \{(t,\, 1-t) \mid t \in [0.2, 0.6]\}$$
- **Corners**:
  - $c_{1,\beta}^{(1)} = (0.2,\, 0.8)$
  - $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$

#### $\mathcal{P}_1(q_1, \alpha)$ and $\mathcal{P}_1(r_1, \beta)$

- $\mathcal{P}_1(q_1,\alpha) = \{(1.0,\, 0.0)\}$ (self-loop)
- $\mathcal{P}_1(r_1,\beta) = \{(0.0,\, 1.0)\}$ (self-loop)

---

### 2.2 $\mathcal{M}_2$

#### $\mathcal{P}_2(p_2, \gamma)$

Let $p(q_2) = t$. Constraints:
- $0.1 \leq t \leq 0.8$
- $0.1 \leq 1-t \leq 0.8 \;\Rightarrow\; 0.2 \leq t \leq 0.9$

Intersection gives $t \in [0.2, 0.8]$.

- **Feasible set**:
  $$\mathcal{P}_2(p_2,\gamma) = \{(t,\, 1-t) \mid t \in [0.2, 0.8]\}$$
- **Corners**:
  - $c_{2,\gamma}^{(1)} = (0.2,\, 0.8)$
  - $c_{2,\gamma}^{(2)} = (0.8,\, 0.2)$

#### $\mathcal{P}_2(p_2, \delta)$

Let $p(q_2) = t$. Constraints:
- $0.1 \leq t \leq 0.4$
- $0.4 \leq 1-t \leq 0.8 \;\Rightarrow\; 0.2 \leq t \leq 0.6$

Intersection gives $t \in [0.2, 0.4]$.

- **Feasible set**:
  $$\mathcal{P}_2(p_2,\delta) = \{(t,\, 1-t) \mid t \in [0.2, 0.4]\}$$
- **Corners**:
  - $c_{2,\delta}^{(1)} = (0.2,\, 0.8)$
  - $c_{2,\delta}^{(2)} = (0.4,\, 0.6)$

#### $\mathcal{P}_2(q_2, \gamma)$ and $\mathcal{P}_2(r_2, \delta)$

- $\mathcal{P}_2(q_2,\gamma) = \{(1.0,\, 0.0)\}$ (self-loop)
- $\mathcal{P}_2(r_2,\delta) = \{(0.0,\, 1.0)\}$ (self-loop)

---

## 3. Running Example 1: Approximate Simulation Relation Verification

**Candidate relation**:
$$\mathcal{R} = \{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\}$$

---

### 3.1 Cooperative Semantics ($\mathcal{M}_2 \preceq_\varepsilon^\forall \mathcal{M}_1$), $\varepsilon = 0$

Verification condition: For every $(x_1,x_2) \in \mathcal{R}$, every $a_1 \in A_1$, every $\mu_1 \in \mathcal{P}_1(x_1,a_1)$, there exist $a_2 \in A_2$ and $\mu_2 \in \mathcal{P}_2(x_2,a_2)$ such that $(\mu_1, \mu_2) \in \overline{\mathcal{R}}_0$ (exact coupling).

#### Check $(p_1, p_2)$

**(a) $a_1 = \alpha$**:
- $\mathcal{P}_1(p_1,\alpha) = [0.4, 0.7]$ (expressed as $q_1$ probability).
- Take $a_2 = \gamma$, $\mathcal{P}_2(p_2,\gamma) = [0.2, 0.8]$.
- Since $[0.4, 0.7] \subseteq [0.2, 0.8]$, for any $\mu_1 \in \mathcal{P}_1(p_1,\alpha)$, take $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\gamma)$.
- Coupling: $\mathcal{W}(q_1,q_2) = \mu_1(q_1)$, $\mathcal{W}(r_1,r_2) = \mu_1(r_1)$, others 0.
- $\mathcal{W}(\mathcal{R}) = 1 \geq 1$. **Satisfied**.

**(b) $a_1 = \beta$**:
- $\mathcal{P}_1(p_1,\beta) = [0.2, 0.6]$.
- Similarly take $a_2 = \gamma$, $[0.2, 0.6] \subseteq [0.2, 0.8]$.
- For any $\mu_1 \in \mathcal{P}_1(p_1,\beta)$, take $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\gamma)$, exact coupling holds.
- **Satisfied**.

Self-loops of $(q_1,q_2)$ and $(r_1,r_2)$ are trivial.

**Conclusion**: $\mathcal{M}_2 \preceq_0^\forall \mathcal{M}_1$ holds, and the maximum relation includes $(p_1,p_2)$.

---

### 3.2 Competitive Semantics ($\mathcal{M}_2 \preceq_\varepsilon^{\forall\exists} \mathcal{M}_1$), $\varepsilon = 0$

Verification condition: For every $(x_1,x_2) \in \mathcal{R}$, every $a_2 \in A_2$, there exists $a_1 \in A_1$ such that for every $\mu_1 \in \mathcal{P}_1(x_1,a_1)$, there exists $\mu_2 \in \mathcal{P}_2(x_2,a_2)$ satisfying exact coupling.

#### Check $(p_1, p_2)$

**(a) $a_2 = \gamma$**:
- Try $a_1 = \alpha$, $\mathcal{P}_1(p_1,\alpha) = [0.4, 0.7]$.
- $\mathcal{P}_2(p_2,\gamma) = [0.2, 0.8]$, $[0.4, 0.7] \subseteq [0.2, 0.8]$.
- For any $\mu_1$, take $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\gamma)$, exact coupling holds.
- **Defense successful**.

**(b) $a_2 = \delta$**:
- $\mathcal{P}_2(p_2,\delta) = [0.2, 0.4]$ (narrow interval).
- Try $a_1 = \alpha$: $\mathcal{P}_1(p_1,\alpha) = [0.4, 0.7]$.
  - $[0.4, 0.7] \not\subseteq [0.2, 0.4]$ (e.g., corner $\mu_1=(0.7,0.3)$ has $q_1$ probability 0.7 exceeding the upper bound 0.4).
  - **Fails**.
- Try $a_1 = \beta$: $\mathcal{P}_1(p_1,\beta) = [0.2, 0.6]$.
  - $[0.2, 0.6] \not\subseteq [0.2, 0.4]$ (corner $\mu_1=(0.6,0.4)$ has $q_1$ probability 0.6 exceeding the upper bound 0.4).
  - **Fails**.
- No $a_1$ can cover all feasible distributions of $a_2=\delta$.

**Conclusion**: $\mathcal{M}_2 \preceq_0^{\forall\exists} \mathcal{M}_1$ **does NOT hold**; $(p_1,p_2)$ is removed under $\varepsilon=0$.

> **Intuitive explanation**: Under Competitive semantics, the abstract controller $\pi_2$ chooses $a_2=\delta$ first, and the concrete system must find an $a_1$ to "cover" it. But $\delta$'s feasible set is too narrow ($q_2$ probability only $[0.2,0.4]$), while M1's two actions are either overall too high ($\alpha$) or have a range that is too wide ($\beta$ upper bound 0.6), neither of which can be fully contained within $[0.2,0.4]$.

---

### 3.3 Competitive Semantics, $\varepsilon = 0.2$

Now we allow a deviation of $\varepsilon=0.2$ per step in the coupling, i.e., requiring $\mathcal{W}(\mathcal{R}) \geq 1 - \varepsilon = 0.8$.

Re-examining $a_2 = \delta$:

- **Try $a_1 = \alpha$**:
  - Corner $\mu_1 = (0.7, 0.3)$: For any $\mu_2 = (t, 1-t) \in \mathcal{P}_2(p_2,\delta)$ ($t \in [0.2, 0.4]$),
    - The optimal coupling aligns $q_1$ mass with $q_2$ and $r_1$ mass with $r_2$:
    - $\mathcal{W}(\mathcal{R}) = \min(0.7, t) + \min(0.3, 1-t)$.
    - Maximum is achieved at $t=0.4$: $0.4 + 0.3 = 0.7 < 0.8$.
  - **Cannot defend**.

- **Try $a_1 = \beta$**:
  - $\mathcal{P}_1(p_1,\beta) = [0.2, 0.6]$, corners are $(0.2, 0.8)$ and $(0.6, 0.4)$.
  - **Corner $\mu_1 = (0.2, 0.8)$**:
    - Take $\mu_2 = (0.2, 0.8) \in \mathcal{P}_2(p_2,\delta)$ (exactly the lower-bound corner of $\delta$).
    - Coupling: $\mathcal{W}(q_1,q_2)=0.2$, $\mathcal{W}(r_1,r_2)=0.8$, $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$. **Satisfied**.
  - **Corner $\mu_1 = (0.6, 0.4)$**:
    - Need to find $\mu_2$ in $\mathcal{P}_2(p_2,\delta)$ such that coupling mass $\geq 0.8$.
    - Take $\mu_2 = (0.4, 0.6)$ (the upper-bound corner of $\delta$).
    - Construct coupling:
      - $\mathcal{W}(q_1,q_2) = 0.4$ (of the 0.6 from $q_1$, 0.4 goes to $q_2$)
      - $\mathcal{W}(q_1,r_2) = 0.2$ (remaining $q_1$ mass)
      - $\mathcal{W}(r_1,q_2) = 0$ (all 0.4 of $r_1$ goes to $r_2$)
      - $\mathcal{W}(r_1,r_2) = 0.4$
    - Verify marginals:
      - Rows: $0.4+0.2=0.6$ ($q_1$), $0+0.4=0.4$ ($r_1$) ✓
      - Columns: $0.4+0=0.4$ ($q_2$), $0.2+0.4=0.6$ ($r_2$) ✓
    - $\mathcal{W}(\mathcal{R}) = \mathcal{W}(q_1,q_2) + \mathcal{W}(r_1,r_2) = 0.4 + 0.4 = 0.8 \geq 0.8$. **Satisfied**.
  - By convexity, all intermediate distributions in $[0.2,0.6]$ can be matched via convex combinations of $\mu_2$.

**Conclusion**: Choosing $a_1 = \beta$ successfully defends against $a_2 = \delta$, and $\mathcal{M}_2 \preceq_{0.2}^{\forall\exists} \mathcal{M}_1$ holds.

> **Key observation**: Under Competitive semantics, the Interface must choose $a_1 = \beta$ rather than $a_1 = \alpha$. $\beta$'s feasible set is wider and extends further downward, so corner $(0.2, 0.8)$ falls exactly within $\delta$'s feasible set, while corner $(0.6, 0.4)$ reaches the $0.8$ threshold exactly through coupling relaxation. This illustrates the trade-off between "action selection" and "probability deviation" in approximate simulation.

---

## 4. Running Example 2: Algorithm 1 (Cooperative, $\varepsilon = 0$)

**Input**: $\mathcal{M}_1, \mathcal{M}_2$, threshold $\varepsilon = 0$.

**Initialization**:
$$\mathcal{R} \leftarrow \{(x_1,x_2) \in X_1 \times X_2 \mid L_1(x_1) = L_2(x_2)\} = \{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\}$$

### Iteration 1

Check $(p_1, p_2)$:

- **$a_1 = \alpha$**, corners $c_{1,\alpha}^{(1)}=(0.4,0.6)$, $c_{1,\alpha}^{(2)}=(0.7,0.3)$:
  - Try $a_2 = \gamma$: Both corners fall within $\mathcal{P}_2(p_2,\gamma)=[0.2,0.8]$.
    - $c_{1,\alpha}^{(1)}$: Take $\mu_2=(0.4,0.6)$, exact coupling, $\mathcal{W}(\mathcal{R})=1.0 \geq 1.0$.
    - $c_{1,\alpha}^{(2)}$: Take $\mu_2=(0.7,0.3)$, exact coupling, $\mathcal{W}(\mathcal{R})=1.0 \geq 1.0$.
  - All corners feasible.

- **$a_1 = \beta$**, corners $c_{1,\beta}^{(1)}=(0.2,0.8)$, $c_{1,\beta}^{(2)}=(0.6,0.4)$:
  - Try $a_2 = \gamma$: Both corners fall within $[0.2,0.8]$.
    - $c_{1,\beta}^{(1)}$: Take $\mu_2=(0.2,0.8)$, $\mathcal{W}(\mathcal{R})=1.0$.
    - $c_{1,\beta}^{(2)}$: Take $\mu_2=(0.6,0.4)$, $\mathcal{W}(\mathcal{R})=1.0$.
  - All corners feasible.

Check $(q_1, q_2)$: Self-loop, trivial, retained.

Check $(r_1, r_2)$: Self-loop, trivial, retained.

**Removed this round**: $\emptyset$.

### Iteration 2
$\mathcal{R}$ unchanged, algorithm terminates.

**Output**:
$$\mathcal{R} = \{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\}$$

---

## 5. Running Example 3: Algorithm 2 (Competitive, $\varepsilon = 0.2$)

**Input**: $\mathcal{M}_1, \mathcal{M}_2$, threshold $\varepsilon = 0.2$.

**Initialization**:
$$\mathcal{R} \leftarrow \{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\}$$

### Iteration 1

Check $(p_1, p_2)$:

- **$a_2 = \gamma$**:
  - Try $a_1 = \alpha$:
    - $c_{1,\alpha}^{(1)}=(0.4,0.6)$: Take $\mu_2=(0.4,0.6) \in \mathcal{P}_2(\gamma)$, $\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$.
    - $c_{1,\alpha}^{(2)}=(0.7,0.3)$: Take $\mu_2=(0.7,0.3) \in \mathcal{P}_2(\gamma)$ (since $0.7 \leq 0.8$), $\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$.
    - All corners feasible, $found \leftarrow \text{True}$.
  - (No need to try other $a_1$)

- **$a_2 = \delta$**:
  - Try $a_1 = \alpha$:
    - $c_{1,\alpha}^{(1)}=(0.4,0.6)$: Take $\mu_2=(0.4,0.6) \in \mathcal{P}_2(\delta)$, $\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$. **Feasible**.
    - $c_{1,\alpha}^{(2)}=(0.7,0.3)$: For any $\mu_2=(t,1-t)$, $t \in [0.2,0.4]$,
      - Maximum coupling mass: $\min(0.7,t) + \min(0.3,1-t) = t + 0.3$ (when $t \leq 0.4$).
      - Maximum is $0.4 + 0.3 = 0.7 < 0.8$. **Infeasible**.
    - A corner is infeasible, $found \leftarrow \text{False}$.
  - Try $a_1 = \beta$:
    - $c_{1,\beta}^{(1)}=(0.2,0.8)$: Take $\mu_2=(0.2,0.8) \in \mathcal{P}_2(\delta)$, $\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$. **Feasible**.
    - $c_{1,\beta}^{(2)}=(0.6,0.4)$: Take $\mu_2=(0.4,0.6) \in \mathcal{P}_2(\delta)$,
      - $\mathcal{W}(q_1,q_2)=0.4$, $\mathcal{W}(q_1,r_2)=0.2$, $\mathcal{W}(r_1,q_2)=0$, $\mathcal{W}(r_1,r_2)=0.4$.
      - $\mathcal{W}(\mathcal{R}) = 0.4 + 0.4 = 0.8 \geq 0.8$. **Feasible**.
    - All corners feasible, $found \leftarrow \text{True}$.

Check $(q_1, q_2)$: Self-loop, trivial, retained.

Check $(r_1, r_2)$: Self-loop, trivial, retained.

**Removed this round**: $\emptyset$.

### Iteration 2
$\mathcal{R}$ unchanged, algorithm terminates.

**Output**:
$$\mathcal{R} = \{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\}$$

---

## 6. Program Reproduction Tips

### 6.1 Data Structure Definition

```python
# M1
X1 = ['p1', 'q1', 'r1']
A1 = ['alpha', 'beta']
x0_1 = 'p1'

# P1_lower[state][action][next_state], P1_upper[state][action][next_state]
P1_lower = {
    'p1': {
        'alpha': {'q1': 0.2, 'r1': 0.1},
        'beta':  {'q1': 0.1, 'r1': 0.2}
    },
    'q1': {'alpha': {'q1': 1.0}},
    'r1': {'beta':  {'r1': 1.0}}
}
P1_upper = {
    'p1': {
        'alpha': {'q1': 0.7, 'r1': 0.6},
        'beta':  {'q1': 0.6, 'r1': 0.8}
    },
    'q1': {'alpha': {'q1': 1.0}},
    'r1': {'beta':  {'r1': 1.0}}
}

# M2
X2 = ['p2', 'q2', 'r2']
A2 = ['gamma', 'delta']
x0_2 = 'p2'

P2_lower = {
    'p2': {
        'gamma': {'q2': 0.1, 'r2': 0.1},
        'delta': {'q2': 0.1, 'r2': 0.4}
    },
    'q2': {'gamma': {'q2': 1.0}},
    'r2': {'delta':  {'r2': 1.0}}
}
P2_upper = {
    'p2': {
        'gamma': {'q2': 0.8, 'r2': 0.8},
        'delta': {'q2': 0.4, 'r2': 0.8}
    },
    'q2': {'gamma': {'q2': 1.0}},
    'r2': {'delta':  {'r2': 1.0}}
}

# Candidate relation
R = {('p1','p2'), ('q1','q2'), ('r1','r2')}
```

### 6.2 Generating Feasible Set Corners

For each $(x,a)$, let the successor states be $\{s_1, s_2\}$, parameterize $p(s_1)=t$, $p(s_2)=1-t$. Find the closed interval for $t$ from the interval constraints; the endpoints are the corners.

For the actions of $p_1$, the analytical formula:
- $t_{\min} = \max\{ \check{P}(x,a,s_1),\; 1 - \hat{P}(x,a,s_2) \}$
- $t_{\max} = \min\{ \hat{P}(x,a,s_1),\; 1 - \check{P}(x,a,s_2) \}$

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

When reproducing in code, prioritize verifying the following conclusions:

1. **Cooperative $\varepsilon=0$**: $(p_1,p_2)$ retained. Both $a_1=\alpha$ and $a_1=\beta$ map to $a_2=\gamma$, since $[0.4,0.7] \subseteq [0.2,0.8]$ and $[0.2,0.6] \subseteq [0.2,0.8]$.
2. **Competitive $\varepsilon=0$**: $(p_1,p_2)$ removed. Under $a_2=\delta$, neither $a_1=\alpha$ ($[0.4,0.7]$) nor $a_1=\beta$ ($[0.2,0.6]$) can be fully contained within $[0.2,0.4]$.
3. **Competitive $\varepsilon=0.2$**: $(p_1,p_2)$ retained. $a_2=\delta$ must be defended by $a_1=\beta$:
   - corner $(0.2,0.8)$ exactly matches $\mu_2=(0.2,0.8)$;
   - corner $(0.6,0.4)$ takes $\mu_2=(0.4,0.6)$, with coupling mass exactly $0.8$.
4. **Semantic difference in action selection**: Under Cooperative, the Interface maps concrete actions to abstract actions ($\alpha,\beta \to \gamma$); under Competitive, the Interface maps abstract actions to concrete actions ($\gamma \to \alpha$, $\delta \to \beta$).

---

## Appendix: Explicit Coupling LP Example

Take Competitive $\varepsilon=0.2$, $(p_1,\beta)$ vs $(p_2,\delta)$, corner $c_1=(0.6,0.4)$:

**Given**:
- $c_1(q_1)=0.6,\; c_1(r_1)=0.4$
- $C(p_2,\delta) = \{(0.2,0.8),\; (0.4,0.6)\}$

**Variables**: $\mathcal{W}_{qq}, \mathcal{W}_{qr}, \mathcal{W}_{rq}, \mathcal{W}_{rr}, \beta_1, \beta_2$

**Constraints**:

```text
# M1 marginal (row sums)
W_qq + W_qr = 0.6
W_rq + W_rr = 0.4

# M2 marginal (column sums = convex combination of corners)
W_qq + W_rq = 0.2*beta_1 + 0.4*beta_2
W_qr + W_rr = 0.8*beta_1 + 0.6*beta_2

# Relation mass
W_qq + W_rr >= 0.8

# Convex combination
beta_1 + beta_2 = 1
beta_1, beta_2 >= 0

# Non-negativity
W_qq, W_qr, W_rq, W_rr >= 0
```

**Feasible solution**: Take $\beta_1=0, \beta_2=1$ (i.e., $\mu_2=(0.4,0.6)$), then:
- Column constraints: $W_qq + W_rq = 0.4$, $W_qr + W_rr = 0.6$.
- Combined with row constraints: $W_qq = 0.4,\; W_qr = 0.2,\; W_rq = 0,\; W_rr = 0.4$.
- Verification: $W_qq + W_rr = 0.4 + 0.4 = 0.8 \geq 0.8$.
- All variables non-negative, all constraints satisfied.

If we take $\beta_1=1, \beta_2=0$ (i.e., $\mu_2=(0.2,0.8)$), then:
- Column constraints: $W_qq + W_rq = 0.2$, $W_qr + W_rr = 0.8$.
- Combined with row constraints: $W_qq = 0.2,\; W_qr = 0.4,\; W_rq = 0,\; W_rr = 0.4$.
- $W_qq + W_rr = 0.2 + 0.4 = 0.6 < 0.8$, **infeasible**.
- This shows that corner $(0.4,0.6)$ is the unique matching that can defend against this adversarial corner.
