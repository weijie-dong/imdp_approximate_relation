# IMDP 近似互模拟案例 — 手工推导与程序复现文档

> **案例设计意图**：本案例中的两个 IMDP 模型参数均为**固定区间**，不随 $\varepsilon$ 改变。近似关系不是通过"修改模型"得到，而是通过**耦合的松弛**自然涌现。案例清晰展示了：
> - Cooperative 语义下，$\varepsilon=0$ 精确成立；
> - Competitive 语义下，$\varepsilon=0$ 精确不成立，但 $\varepsilon=0.2$ 近似成立；
> - 同一对状态 $(p_1,p_2)$ 在不同语义下呈现截然不同的行为，凸显了 Interface 块选择动作的关键作用。

---

## 1. 模型定义

### 1.1 IMDP $\mathcal{M}_1$（Concrete）

- **状态集**：$X_1 = \\{p_1, q_1, r_1\\}$
- **初始状态**：$x_0^1 = p_1$
- **动作集**：$A_1 = \\{\alpha, \beta\\}$
- **原子命题**：$\mathcal{AP}_1 = \\{G, U\\}$
- **标签函数**：
  - $L_1(p_1) = \emptyset$
  - $L_1(q_1) = \\{G\\}$
  - $L_1(r_1) = \\{U\\}$

**转移概率区间**：

| 当前状态 | 动作 | 后继状态 | 下界 $\check{P}_1$ | 上界 $\hat{P}_1$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_1$ | $\alpha$ | $q_1$ | 0.2 | 0.7 |
| $p_1$ | $\alpha$ | $r_1$ | 0.1 | 0.6 |
| $p_1$ | $\beta$ | $q_1$ | 0.1 | 0.6 |
| $p_1$ | $\beta$ | $r_1$ | 0.2 | 0.8 |
| $q_1$ | $\alpha$ | $q_1$ | 1.0 | 1.0 |
| $r_1$ | $\beta$ | $r_1$ | 1.0 | 1.0 |

---

### 1.2 IMDP $\mathcal{M}_2$（Abstract）

- **状态集**：$X_2 = \\{p_2, q_2, r_2\\}$
- **初始状态**：$x_0^2 = p_2$
- **动作集**：$A_2 = \\{\gamma, \delta\\}$
- **原子命题**：$\mathcal{AP}_2 = \\{G, U\\}$
- **标签函数**：
  - $L_2(p_2) = \emptyset$
  - $L_2(q_2) = \\{G\\}$
  - $L_2(r_2) = \\{U\\}$

**转移概率区间**：

| 当前状态 | 动作 | 后继状态 | 下界 $\check{P}_2$ | 上界 $\hat{P}_2$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_2$ | $\gamma$ | $q_2$ | 0.1 | 0.8 |
| $p_2$ | $\gamma$ | $r_2$ | 0.1 | 0.8 |
| $p_2$ | $\delta$ | $q_2$ | 0.1 | 0.4 |
| $p_2$ | $\delta$ | $r_2$ | 0.4 | 0.8 |
| $q_2$ | $\gamma$ | $q_2$ | 1.0 | 1.0 |
| $r_2$ | $\delta$ | $r_2$ | 1.0 | 1.0 |

---

## 2. Feasible Sets 解析推导

### 2.1 $\mathcal{M}_1$

#### $\mathcal{P}_1(p_1, \alpha)$

设 $p(q_1) = t$，则 $p(r_1) = 1-t$。约束为：
- $0.2 \leq t \leq 0.7$
- $0.1 \leq 1-t \leq 0.6 \;\Rightarrow\; 0.4 \leq t \leq 0.9$

取交集得 $t \in [0.4, 0.7]$。

- **Feasible set**：
  $$\mathcal{P}_1(p_1,\alpha) = \\{(t,\, 1-t) \mid t \in [0.4, 0.7]\\}$$
- **Corners**：
  - $c_{1,\alpha}^{(1)} = (0.4,\, 0.6)$
  - $c_{1,\alpha}^{(2)} = (0.7,\, 0.3)$

#### $\mathcal{P}_1(p_1, \beta)$

设 $p(q_1) = t$。约束为：
- $0.1 \leq t \leq 0.6$
- $0.2 \leq 1-t \leq 0.8 \;\Rightarrow\; 0.2 \leq t \leq 0.8$

取交集得 $t \in [0.2, 0.6]$。

- **Feasible set**：
  $$\mathcal{P}_1(p_1,\beta) = \\{(t,\, 1-t) \mid t \in [0.2, 0.6]\\}$$
- **Corners**：
  - $c_{1,\beta}^{(1)} = (0.2,\, 0.8)$
  - $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$

#### $\mathcal{P}_1(q_1, \alpha)$ 与 $\mathcal{P}_1(r_1, \beta)$

- $\mathcal{P}_1(q_1,\alpha) = \\{(1.0,\, 0.0)\\}$（自环）
- $\mathcal{P}_1(r_1,\beta) = \\{(0.0,\, 1.0)\\}$（自环）

---

### 2.2 $\mathcal{M}_2$

#### $\mathcal{P}_2(p_2, \gamma)$

设 $p(q_2) = t$。约束为：
- $0.1 \leq t \leq 0.8$
- $0.1 \leq 1-t \leq 0.8 \;\Rightarrow\; 0.2 \leq t \leq 0.9$

取交集得 $t \in [0.2, 0.8]$。

- **Feasible set**：
  $$\mathcal{P}_2(p_2,\gamma) = \\{(t,\, 1-t) \mid t \in [0.2, 0.8]\\}$$
- **Corners**：
  - $c_{2,\gamma}^{(1)} = (0.2,\, 0.8)$
  - $c_{2,\gamma}^{(2)} = (0.8,\, 0.2)$

#### $\mathcal{P}_2(p_2, \delta)$

设 $p(q_2) = t$。约束为：
- $0.1 \leq t \leq 0.4$
- $0.4 \leq 1-t \leq 0.8 \;\Rightarrow\; 0.2 \leq t \leq 0.6$

取交集得 $t \in [0.2, 0.4]$。

- **Feasible set**：
  $$\mathcal{P}_2(p_2,\delta) = \\{(t,\, 1-t) \mid t \in [0.2, 0.4]\\}$$
- **Corners**：
  - $c_{2,\delta}^{(1)} = (0.2,\, 0.8)$
  - $c_{2,\delta}^{(2)} = (0.4,\, 0.6)$

#### $\mathcal{P}_2(q_2, \gamma)$ 与 $\mathcal{P}_2(r_2, \delta)$

- $\mathcal{P}_2(q_2,\gamma) = \\{(1.0,\, 0.0)\\}$（自环）
- $\mathcal{P}_2(r_2,\delta) = \\{(0.0,\, 1.0)\\}$（自环）

---

## 3. Running Example 1：近似模拟关系验证

**候选关系**：
$$\mathcal{R} = \\{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\\}$$

---

### 3.1 Cooperative 语义（$\mathcal{M}_2 \preceq_\varepsilon^\forall \mathcal{M}_1$），$\varepsilon = 0$

验证条件：对任意 $(x_1,x_2) \in \mathcal{R}$，任意 $a_1 \in A_1$，任意 $\mu_1 \in \mathcal{P}_1(x_1,a_1)$，存在 $a_2 \in A_2$ 和 $\mu_2 \in \mathcal{P}_2(x_2,a_2)$，使得 $(\mu_1, \mu_2) \in \overline{\mathcal{R}}_0$（精确耦合）。

#### 检查 $(p_1, p_2)$

**（a）$a_1 = \alpha$**：
- $\mathcal{P}_1(p_1,\alpha) = [0.4, 0.7]$（以 $q_1$ 概率表示）。
- 取 $a_2 = \gamma$，$\mathcal{P}_2(p_2,\gamma) = [0.2, 0.8]$。
- 由于 $[0.4, 0.7] \subseteq [0.2, 0.8]$，对任意 $\mu_1 \in \mathcal{P}_1(p_1,\alpha)$，取 $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\gamma)$。
- 耦合：$\mathcal{W}(q_1,q_2) = \mu_1(q_1)$，$\mathcal{W}(r_1,r_2) = \mu_1(r_1)$，其余为 0。
- $\mathcal{W}(\mathcal{R}) = 1 \geq 1$。**满足**。

**（b）$a_1 = \beta$**：
- $\mathcal{P}_1(p_1,\beta) = [0.2, 0.6]$。
- 同样取 $a_2 = \gamma$，$[0.2, 0.6] \subseteq [0.2, 0.8]$。
- 对任意 $\mu_1 \in \mathcal{P}_1(p_1,\beta)$，取 $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\gamma)$，精确耦合成立。
- **满足**。

$(q_1,q_2)$ 与 $(r_1,r_2)$ 的自环 trivial。

**结论**：$\mathcal{M}_2 \preceq_0^\forall \mathcal{M}_1$ 成立，最大关系包含 $(p_1,p_2)$。

---

### 3.2 Competitive 语义（$\mathcal{M}_2 \preceq_\varepsilon^{\forall\exists} \mathcal{M}_1$），$\varepsilon = 0$

验证条件：对任意 $(x_1,x_2) \in \mathcal{R}$，任意 $a_2 \in A_2$，存在 $a_1 \in A_1$，使得对任意 $\mu_1 \in \mathcal{P}_1(x_1,a_1)$，存在 $\mu_2 \in \mathcal{P}_2(x_2,a_2)$ 满足精确耦合。

#### 检查 $(p_1, p_2)$

**（a）$a_2 = \gamma$**：
- 尝试 $a_1 = \alpha$，$\mathcal{P}_1(p_1,\alpha) = [0.4, 0.7]$。
- $\mathcal{P}_2(p_2,\gamma) = [0.2, 0.8]$，$[0.4, 0.7] \subseteq [0.2, 0.8]$。
- 对任意 $\mu_1$，取 $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\gamma)$，精确耦合成立。
- **防御成功**。

**（b）$a_2 = \delta$**：
- $\mathcal{P}_2(p_2,\delta) = [0.2, 0.4]$（窄区间）。
- 尝试 $a_1 = \alpha$：$\mathcal{P}_1(p_1,\alpha) = [0.4, 0.7]$。
  - $[0.4, 0.7] \not\subseteq [0.2, 0.4]$（例如 corner $\mu_1=(0.7,0.3)$ 的 $q_1$ 概率 0.7 超出上界 0.4）。
  - **失败**。
- 尝试 $a_1 = \beta$：$\mathcal{P}_1(p_1,\beta) = [0.2, 0.6]$。
  - $[0.2, 0.6] \not\subseteq [0.2, 0.4]$（corner $\mu_1=(0.6,0.4)$ 的 $q_1$ 概率 0.6 超出上界 0.4）。
  - **失败**。
- 无 $a_1$ 能覆盖 $a_2=\delta$ 的所有 feasible 分布。

**结论**：$\mathcal{M}_2 \preceq_0^{\forall\exists} \mathcal{M}_1$ **不成立**，$(p_1,p_2)$ 在 $\varepsilon=0$ 下被移除。

> **直观解释**：Competitive 语义下，abstract 控制器 $\pi_2$ 先选 $a_2=\delta$，concrete 系统必须找一个 $a_1$ 来"兜底"。但 $\delta$ 的 feasible set 太窄（$q_2$ 概率仅 $[0.2,0.4]$），而 M1 的两个动作要么整体偏高（$\alpha$），要么范围太宽（$\beta$ 上限 0.6），都无法完全落入 $[0.2,0.4]$ 内。

---

### 3.3 Competitive 语义，$\varepsilon = 0.2$

现在允许每步耦合有 $\varepsilon=0.2$ 的偏差，即要求 $\mathcal{W}(\mathcal{R}) \geq 1 - \varepsilon = 0.8$。

重新检查 $a_2 = \delta$：

- **尝试 $a_1 = \alpha$**：
  - Corner $\mu_1 = (0.7, 0.3)$：对任意 $\mu_2 = (t, 1-t) \in \mathcal{P}_2(p_2,\delta)$（$t \in [0.2, 0.4]$），
    - 最优耦合将 $q_1$ 质量与 $q_2$ 对齐，$r_1$ 质量与 $r_2$ 对齐：
    - $\mathcal{W}(\mathcal{R}) = \min(0.7, t) + \min(0.3, 1-t)$。
    - 当 $t=0.4$ 时取得最大值 $0.4 + 0.3 = 0.7 < 0.8$。
  - **无法防御**。

- **尝试 $a_1 = \beta$**：
  - $\mathcal{P}_1(p_1,\beta) = [0.2, 0.6]$，corners 为 $(0.2, 0.8)$ 与 $(0.6, 0.4)$。
  - **Corner $\mu_1 = (0.2, 0.8)$**：
    - 取 $\mu_2 = (0.2, 0.8) \in \mathcal{P}_2(p_2,\delta)$（恰好是 $\delta$ 的下界 corner）。
    - 耦合：$\mathcal{W}(q_1,q_2)=0.2$，$\mathcal{W}(r_1,r_2)=0.8$，$\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$。**满足**。
  - **Corner $\mu_1 = (0.6, 0.4)$**：
    - 需在 $\mathcal{P}_2(p_2,\delta)$ 中找到 $\mu_2$ 使耦合质量 $\geq 0.8$。
    - 取 $\mu_2 = (0.4, 0.6)$（$\delta$ 的上界 corner）。
    - 构造耦合：
      - $\mathcal{W}(q_1,q_2) = 0.4$（$q_1$ 的 0.6 中取 0.4 给 $q_2$）
      - $\mathcal{W}(q_1,r_2) = 0.2$（剩余 $q_1$ 质量）
      - $\mathcal{W}(r_1,q_2) = 0$（$r_1$ 的 0.4 全部给 $r_2$）
      - $\mathcal{W}(r_1,r_2) = 0.4$
    - 验证边际：
      - 行：$0.4+0.2=0.6$（$q_1$），$0+0.4=0.4$（$r_1$）✓
      - 列：$0.4+0=0.4$（$q_2$），$0.2+0.4=0.6$（$r_2$）✓
    - $\mathcal{W}(\mathcal{R}) = \mathcal{W}(q_1,q_2) + \mathcal{W}(r_1,r_2) = 0.4 + 0.4 = 0.8 \geq 0.8$。**满足**。
  - 由凸性，$[0.2,0.6]$ 内所有中间分布均可通过 $\mu_2$ 的凸组合实现匹配。

**结论**：选择 $a_1 = \beta$ 可成功防御 $a_2 = \delta$，$\mathcal{M}_2 \preceq_{0.2}^{\forall\exists} \mathcal{M}_1$ 成立。

> **关键观察**：Competitive 语义下 Interface 必须选择 $a_1 = \beta$ 而非 $a_1 = \alpha$。$\beta$ 的 feasible set 更宽且向下延伸，使得 corner $(0.2, 0.8)$ 能精确落入 $\delta$ 的 feasible set，而 corner $(0.6, 0.4)$ 通过耦合松弛恰好达到 $0.8$ 的阈值。这体现了近似模拟中"动作选择"与"概率偏差"的权衡。

---

## 4. Running Example 2：Algorithm 1（Cooperative，$\varepsilon = 0$）

**输入**：$\mathcal{M}_1, \mathcal{M}_2$，阈值 $\varepsilon = 0$。

**初始化**：
$$\mathcal{R} \leftarrow \\{(x_1,x_2) \in X_1 \times X_2 \mid L_1(x_1) = L_2(x_2)\\} = \\{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\\}$$

### Iteration 1

检查 $(p_1, p_2)$：

- **$a_1 = \alpha$**，corners $c_{1,\alpha}^{(1)}=(0.4,0.6)$，$c_{1,\alpha}^{(2)}=(0.7,0.3)$：
  - 尝试 $a_2 = \gamma$：两个 corners 均落在 $\mathcal{P}_2(p_2,\gamma)=[0.2,0.8]$ 内。
    - $c_{1,\alpha}^{(1)}$：取 $\mu_2=(0.4,0.6)$，精确耦合，$\mathcal{W}(\mathcal{R})=1.0 \geq 1.0$。
    - $c_{1,\alpha}^{(2)}$：取 $\mu_2=(0.7,0.3)$，精确耦合，$\mathcal{W}(\mathcal{R})=1.0 \geq 1.0$。
  - 所有 corners 可行。

- **$a_1 = \beta$**，corners $c_{1,\beta}^{(1)}=(0.2,0.8)$，$c_{1,\beta}^{(2)}=(0.6,0.4)$：
  - 尝试 $a_2 = \gamma$：两个 corners 均落在 $[0.2,0.8]$ 内。
    - $c_{1,\beta}^{(1)}$：取 $\mu_2=(0.2,0.8)$，$\mathcal{W}(\mathcal{R})=1.0$。
    - $c_{1,\beta}^{(2)}$：取 $\mu_2=(0.6,0.4)$，$\mathcal{W}(\mathcal{R})=1.0$。
  - 所有 corners 可行。

检查 $(q_1, q_2)$：自环，trivial，保留。

检查 $(r_1, r_2)$：自环，trivial，保留。

**本轮移除**：$\emptyset$。

### Iteration 2
$\mathcal{R}$ 未变化，算法终止。

**输出**：
$$\mathcal{R} = \\{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\\}$$

---

## 5. Running Example 3：Algorithm 2（Competitive，$\varepsilon = 0.2$）

**输入**：$\mathcal{M}_1, \mathcal{M}_2$，阈值 $\varepsilon = 0.2$。

**初始化**：
$$\mathcal{R} \leftarrow \\{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\\}$$

### Iteration 1

检查 $(p_1, p_2)$：

- **$a_2 = \gamma$**：
  - 尝试 $a_1 = \alpha$：
    - $c_{1,\alpha}^{(1)}=(0.4,0.6)$：取 $\mu_2=(0.4,0.6) \in \mathcal{P}_2(\gamma)$，$\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$。
    - $c_{1,\alpha}^{(2)}=(0.7,0.3)$：取 $\mu_2=(0.7,0.3) \in \mathcal{P}_2(\gamma)$（因 $0.7 \leq 0.8$），$\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$。
    - 所有 corners 可行，$found \leftarrow \text{True}$。
  - （无需尝试其他 $a_1$）

- **$a_2 = \delta$**：
  - 尝试 $a_1 = \alpha$：
    - $c_{1,\alpha}^{(1)}=(0.4,0.6)$：取 $\mu_2=(0.4,0.6) \in \mathcal{P}_2(\delta)$，$\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$。**可行**。
    - $c_{1,\alpha}^{(2)}=(0.7,0.3)$：对任意 $\mu_2=(t,1-t)$，$t \in [0.2,0.4]$，
      - 耦合质量最大值：$\min(0.7,t) + \min(0.3,1-t) = t + 0.3$（当 $t \leq 0.4$）。
      - 最大值为 $0.4 + 0.3 = 0.7 < 0.8$。**不可行**。
    - 存在 corner 不可行，$found \leftarrow \text{False}$。
  - 尝试 $a_1 = \beta$：
    - $c_{1,\beta}^{(1)}=(0.2,0.8)$：取 $\mu_2=(0.2,0.8) \in \mathcal{P}_2(\delta)$，$\mathcal{W}(\mathcal{R})=1.0 \geq 0.8$。**可行**。
    - $c_{1,\beta}^{(2)}=(0.6,0.4)$：取 $\mu_2=(0.4,0.6) \in \mathcal{P}_2(\delta)$，
      - $\mathcal{W}(q_1,q_2)=0.4$，$\mathcal{W}(q_1,r_2)=0.2$，$\mathcal{W}(r_1,q_2)=0$，$\mathcal{W}(r_1,r_2)=0.4$。
      - $\mathcal{W}(\mathcal{R}) = 0.4 + 0.4 = 0.8 \geq 0.8$。**可行**。
    - 所有 corners 可行，$found \leftarrow \text{True}$。

检查 $(q_1, q_2)$：自环，trivial，保留。

检查 $(r_1, r_2)$：自环，trivial，保留。

**本轮移除**：$\emptyset$。

### Iteration 2
$\mathcal{R}$ 未变化，算法终止。

**输出**：
$$\mathcal{R} = \\{(p_1,p_2),\; (q_1,q_2),\; (r_1,r_2)\\}$$

---

## 6. 程序复现提示

### 6.1 数据结构定义

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

# 候选关系
R = {('p1','p2'), ('q1','q2'), ('r1','r2')}
```

### 6.2 Feasible Set Corners 生成

对每个 $(x,a)$，设后继状态为 $\\{s_1, s_2\\}$，参数化 $p(s_1)=t$，$p(s_2)=1-t$。由区间约束求 $t$ 的闭区间，端点即为 corners。

对 $p_1$ 的动作，解析公式：
- $t_{\min} = \max\\{ \check{P}(x,a,s_1),\; 1 - \hat{P}(x,a,s_2) \\}$
- $t_{\max} = \min\\{ \hat{P}(x,a,s_1),\; 1 - \check{P}(x,a,s_2) \\}$

### 6.3 Coupling LP（Definition 6）

对给定 corner $c_1 \in C(x_1,a_1)$、动作 $a_2$、阈值 $\varepsilon$：

**变量**：
- $\mathcal{W}(x_1', x_2')$ for all $(x_1', x_2') \in X_1 \times X_2$
- $\beta_i$ for each corner $c_2^i \in C(x_2, a_2)$

**约束**：
1. $\forall x_1' \in X_1: \sum_{x_2'} \mathcal{W}(x_1', x_2') = c_1(x_1')$
2. $\forall x_2' \in X_2: \sum_{x_1'} \mathcal{W}(x_1', x_2') = \sum_{i} \beta_i \cdot c_2^i(x_2')$
3. $\sum_{(x_1',x_2') \in \mathcal{R}} \mathcal{W}(x_1', x_2') \geq 1 - \varepsilon$
4. $\sum_{i} \beta_i = 1,\; \beta_i \geq 0$
5. $\mathcal{W} \geq 0$

### 6.4 关键核对点

程序复现时应优先验证以下结论：

1. **Cooperative $\varepsilon=0$**：$(p_1,p_2)$ 保留。$a_1=\alpha$ 和 $a_1=\beta$ 均映射到 $a_2=\gamma$，因 $[0.4,0.7] \subseteq [0.2,0.8]$ 且 $[0.2,0.6] \subseteq [0.2,0.8]$。
2. **Competitive $\varepsilon=0$**：$(p_1,p_2)$ 被移除。$a_2=\delta$ 时，$a_1=\alpha$（$[0.4,0.7]$）和 $a_1=\beta$（$[0.2,0.6]$）均无法完全落入 $[0.2,0.4]$。
3. **Competitive $\varepsilon=0.2$**：$(p_1,p_2)$ 保留。$a_2=\delta$ 必须由 $a_1=\beta$ 防御：
   - corner $(0.2,0.8)$ 精确匹配 $\mu_2=(0.2,0.8)$；
   - corner $(0.6,0.4)$ 取 $\mu_2=(0.4,0.6)$，耦合质量恰好为 $0.8$。
4. **动作选择的语义差异**：Cooperative 中 Interface 将 concrete 动作映射到 abstract 动作（$\alpha,\beta \to \gamma$）；Competitive 中 Interface 将 abstract 动作映射到 concrete 动作（$\gamma \to \alpha$，$\delta \to \beta$）。

---

## 附录：Coupling LP 显式示例

以 Competitive $\varepsilon=0.2$ 中 $(p_1,\beta)$ vs $(p_2,\delta)$、corner $c_1=(0.6,0.4)$ 为例：

**已知**：
- $c_1(q_1)=0.6,\; c_1(r_1)=0.4$
- $C(p_2,\delta) = \\{(0.2,0.8),\; (0.4,0.6)\\}$

**变量**：$\mathcal{W}_{qq}, \mathcal{W}_{qr}, \mathcal{W}_{rq}, \mathcal{W}_{rr}, \beta_1, \beta_2$

**约束**：

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

**可行解**：取 $\beta_1=0, \beta_2=1$（即 $\mu_2=(0.4,0.6)$），则：
- 列约束：$W_qq + W_rq = 0.4$，$W_qr + W_rr = 0.6$。
- 结合行约束解得：$W_qq = 0.4,\; W_qr = 0.2,\; W_rq = 0,\; W_rr = 0.4$。
- 验证：$W_qq + W_rr = 0.4 + 0.4 = 0.8 \geq 0.8$。
- 所有变量非负，满足全部约束。

若取 $\beta_1=1, \beta_2=0$（即 $\mu_2=(0.2,0.8)$），则：
- 列约束：$W_qq + W_rq = 0.2$，$W_qr + W_rr = 0.8$。
- 结合行约束：$W_qq = 0.2,\; W_qr = 0.4,\; W_rq = 0,\; W_rr = 0.4$。
- $W_qq + W_rr = 0.2 + 0.4 = 0.6 < 0.8$，**不可行**。
- 这说明 corner $(0.4,0.6)$ 是唯一能防御该 adversarial corner 的匹配。
