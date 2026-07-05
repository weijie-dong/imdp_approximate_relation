# IMDP Running Examples — 复现文档（参数修正版）

&gt; **说明**：本文档中 Fig.3 与 Fig.4 的转移概率区间以用户最新更正为准。所有 feasible set、corner 与耦合构造均基于更正后的参数重新解析推导，若与论文原文中的文字描述不一致，以本文档数值为准。

---

## 1. 模型定义

### 1.1 IMDP $\mathcal{M}_1$ (Fig. 3)

- **状态集**：$X_1 = \{p_1, q_1, r_1\}$
- **初始状态**：$x_0^1 = p_1$
- **动作集**：$A_1 = \{\alpha, \beta\}$
- **原子命题**：$\mathcal{AP}_1 = \{G, U\}$
- **标签函数**：
  - $L_1(p_1) = \emptyset$
  - $L_1(q_1) = \{G\}$
  - $L_1(r_1) = \{U\}$

**转移概率区间**：

| 当前状态 | 动作 | 后继状态 | 下界 $\check{P}_1$ | 上界 $\hat{P}_1$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_1$ | $\alpha$ | $q_1$ | 0.1 | 0.6 |
| $p_1$ | $\alpha$ | $r_1$ | 0.0 | 1.0 |
| $p_1$ | $\beta$ | $q_1$ | 0.0 | 0.6 |
| $p_1$ | $\beta$ | $r_1$ | 0.0 | 1.0 |
| $q_1$ | $\alpha$ | $q_1$ | 1.0 | 1.0 |
| $r_1$ | $\beta$ | $r_1$ | 1.0 | 1.0 |

---

### 1.2 IMDP $\mathcal{M}_2$ (Fig. 4)

- **状态集**：$X_2 = \{p_2, q_2, r_2\}$
- **初始状态**：$x_0^2 = p_2$
- **动作集**：$A_2 = \{\gamma, \delta\}$
- **原子命题**：$\mathcal{AP}_2 = \{G, U\}$
- **标签函数**：
  - $L_2(p_2) = \emptyset$
  - $L_2(q_2) = \{G\}$
  - $L_2(r_2) = \{U\}$

**转移概率区间**（其中 $t \geq 0$ 为可调参数，在近似模拟中对应 $\varepsilon$ 的取值）：

| 当前状态 | 动作 | 后继状态 | 下界 $\check{P}_2$ | 上界 $\hat{P}_2$ |
|:--------:|:----:|:--------:|:------------------:|:----------------:|
| $p_2$ | $\gamma$ | $q_2$ | 0.1 | $0.6+t$ |
| $p_2$ | $\gamma$ | $r_2$ | 0.0 | 1.0 |
| $p_2$ | $\delta$ | $q_2$ | 0.1 | 0.8 |
| $p_2$ | $\delta$ | $r_2$ | 0.0 | 1.0 |
| $q_2$ | $\gamma$ | $q_2$ | 1.0 | 1.0 |
| $r_2$ | $\delta$ | $r_2$ | 1.0 | 1.0 |

---

## 2. Feasible Sets 解析推导

由区间约束与概率归一化条件 $\sum_{x'} p(x') = 1$ 联立，可得各状态-动作对的 feasible set 及其 corners（极值点）。

### 2.1 $\mathcal{M}_1$

#### $\mathcal{P}_1(p_1, \alpha)$

约束：
- $0.1 \leq p(q_1) \leq 0.6$
- $0.0 \leq p(r_1) \leq 1.0$
- $p(q_1) + p(r_1) = 1$

由归一化得 $p(r_1) = 1 - p(q_1) \in [0.4, 0.9]$，与 $p(r_1) \in [0.0, 1.0]$ 取交集得 $p(r_1) \in [0.4, 0.9]$，对应 $p(q_1) \in [0.1, 0.6]$。

- **Feasible set**：
  $$\mathcal{P}_1(p_1,\alpha) = \{(p,\, 1-p) \mid p \in [0.1, 0.6]\}$$
- **Corners**：
  - $c_{1,\alpha}^{(1)} = (0.1,\, 0.9)$  （即 $q_1$ 概率 0.1，$r_1$ 概率 0.9）
  - $c_{1,\alpha}^{(2)} = (0.6,\, 0.4)$

#### $\mathcal{P}_1(p_1, \beta)$

约束：
- $0.0 \leq p(q_1) \leq 0.6$
- $0.0 \leq p(r_1) \leq 1.0$
- $p(q_1) + p(r_1) = 1$

由归一化得 $p(r_1) = 1 - p(q_1) \in [0.4, 1.0]$，与上界 $1.0$ 取交集后仍为 $[0.4, 1.0]$，对应 $p(q_1) \in [0.0, 0.6]$。

- **Feasible set**：
  $$\mathcal{P}_1(p_1,\beta) = \{(p,\, 1-p) \mid p \in [0.0, 0.6]\}$$
- **Corners**：
  - $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$
  - $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$

#### $\mathcal{P}_1(q_1, \alpha)$ 与 $\mathcal{P}_1(r_1, \beta)$

均为自环单点分布：
- $\mathcal{P}_1(q_1,\alpha) = \{(1.0,\, 0.0)\}$
- $\mathcal{P}_1(r_1,\beta) = \{(0.0,\, 1.0)\}$

---

### 2.2 $\mathcal{M}_2$

#### $\mathcal{P}_2(p_2, \gamma)$（参数 $t$）

约束：
- $0.1 \leq p(q_2) \leq 0.6+t$
- $0.0 \leq p(r_2) \leq 1.0$
- $p(q_2) + p(r_2) = 1$

由归一化得 $p(r_2) = 1 - p(q_2)$，且 $p(q_2) \leq 1$（因 $p(r_2) \geq 0$）。故实际 $p(q_2) \in [0.1,\, \min(0.6+t,\, 1)]$，$p(r_2) \in [1-\min(0.6+t,1),\, 0.9]$。

- **当 $t=0$（即 $\varepsilon=0$）时**：
  $$\mathcal{P}_2(p_2,\gamma) = \{(q,\, 1-q) \mid q \in [0.1, 0.6]\}$$
  Corners：$c_{2,\gamma}^{(1)} = (0.1,\, 0.9)$，$c_{2,\gamma}^{(2)} = (0.6,\, 0.4)$

- **当 $t=0.5$（即 $\varepsilon=0.5$）时**：
  上界 $0.6+0.5=1.1$ 被归一化约束截断为 $1.0$，
  $$\mathcal{P}_2(p_2,\gamma) = \{(q,\, 1-q) \mid q \in [0.1, 1.0]\}$$
  Corners：$c_{2,\gamma}^{(1)} = (0.1,\, 0.9)$，$c_{2,\gamma}^{(2)} = (1.0,\, 0.0)$

#### $\mathcal{P}_2(p_2, \delta)$

约束：
- $0.1 \leq p(q_2) \leq 0.8$
- $0.0 \leq p(r_2) \leq 1.0$
- $p(q_2) + p(r_2) = 1$

由归一化得 $p(r_2) = 1 - p(q_2) \in [0.2, 0.9]$，与 $[0.0, 1.0]$ 取交集后仍为 $[0.2, 0.9]$。

- **Feasible set**：
  $$\mathcal{P}_2(p_2,\delta) = \{(q,\, 1-q) \mid q \in [0.1, 0.8]\}$$
- **Corners**：
  - $c_{2,\delta}^{(1)} = (0.1,\, 0.9)$
  - $c_{2,\delta}^{(2)} = (0.8,\, 0.2)$

#### $\mathcal{P}_2(q_2, \gamma)$ 与 $\mathcal{P}_2(r_2, \delta)$

- $\mathcal{P}_2(q_2,\gamma) = \{(1.0,\, 0.0)\}$
- $\mathcal{P}_2(r_2,\delta) = \{(0.0,\, 1.0)\}$

---

## 3. Running Example 1：近似模拟关系验证

**候选关系**：
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

### 3.1 Cooperative 语义（$\mathcal{M}_2 \preceq_\varepsilon^\forall \mathcal{M}_1$），$\varepsilon = 0$

验证条件：对任意 $(x_1,x_2) \in \mathcal{R}$，任意 $a_1 \in A_1$，任意 $\mu_1 \in \mathcal{P}_1(x_1,a_1)$，存在 $a_2 \in A_2$ 和 $\mu_2 \in \mathcal{P}_2(x_2,a_2)$，使得存在耦合 $\mathcal{W}$ 满足 $\mathcal{W}(\mathcal{R}) \geq 1$（即精确匹配）。

#### 检查 $(p_1, p_2)$，动作 $a_1 = \alpha$

- $\mu_1 \in \mathcal{P}_1(p_1,\alpha)$，feasible set 为 $q_1 \in [0.1, 0.6]$。
- 取 abstract 动作 $a_2 = \gamma$（$t=0$），此时 $\mathcal{P}_2(p_2,\gamma)$ 恰好与 $\mathcal{P}_1(p_1,\alpha)$ 重合。
- 对任意 $\mu_1 = (p,\, 1-p)$，取 $\mu_2 = \mu_1 = (p,\, 1-p) \in \mathcal{P}_2(p_2,\gamma)$。
- 耦合构造：$\mathcal{W}(q_1,q_2) = p$，$\mathcal{W}(r_1,r_2) = 1-p$，其余为 0。
- $\mathcal{W}(\mathcal{R}) = 1 \geq 1$。**满足**。

#### 检查 $(p_1, p_2)$，动作 $a_1 = \beta$

- $\mathcal{P}_1(p_1,\beta)$ 包含 corner $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$（即 $q_1$ 概率 0，$r_1$ 概率 1）。
- 对任意 $a_2 \in A_2$：
  - 若 $a_2 = \gamma$（$t=0$）：$\mathcal{P}_2(p_2,\gamma)$ 要求 $q_2 \geq 0.1$，故不存在 $\mu_2$ 使得 $\mu_2(q_2) = 0$。任何耦合都必须将质量 1 放在 $r_1$ 行，但 $r_1$ 只能与 $r_2$ 相关（因 $(r_1,q_2) \notin \mathcal{R}$），而 $\mu_2(r_2) = 1 - \mu_2(q_2) \leq 0.9 &lt; 1$，无法精确匹配。
  - 若 $a_2 = \delta$：同理 $\mathcal{P}_2(p_2,\delta)$ 要求 $q_2 \geq 0.1$，无法精确匹配 $\mu_1 = (0,1)$。
- **结论**：corner $(0.0, 1.0)$ 无法被任何 $a_2$ 精确匹配，因此 $(p_1,p_2)$ **不满足** cooperative $\varepsilon=0$ 条件。

#### 结论（Cooperative $\varepsilon=0$）

最大 cooperative 精确模拟关系为：
$$\mathcal{R} = \{(q_1,q_2),\, (r_1,r_2)\}$$
（$(p_1,p_2)$ 被移除）

---

### 3.2 Competitive 语义（$\mathcal{M}_2 \preceq_\varepsilon^{\forall\exists} \mathcal{M}_1$），$\varepsilon = 0$

验证条件：对任意 $(x_1,x_2) \in \mathcal{R}$，任意 $a_2 \in A_2$，存在 $a_1 \in A_1$，使得对任意 $\mu_1 \in \mathcal{P}_1(x_1,a_1)$，存在 $\mu_2 \in \mathcal{P}_2(x_2,a_2)$ 精确匹配。

#### 检查 $(p_1, p_2)$，$a_2 = \gamma$（$t=0$）

- 尝试 $a_1 = \alpha$：
  - $\mathcal{P}_1(p_1,\alpha)$ 的 corners 为 $(0.1,0.9)$ 与 $(0.6,0.4)$。
  - 对 $\mu_1 = (0.1,0.9)$：取 $\mu_2 = (0.1,0.9) \in \mathcal{P}_2(p_2,\gamma)$，耦合 $\mathcal{W}(q_1,q_2)=0.1$，$\mathcal{W}(r_1,r_2)=0.9$，$\mathcal{W}(\mathcal{R})=1$。
  - 对 $\mu_1 = (0.6,0.4)$：取 $\mu_2 = (0.6,0.4) \in \mathcal{P}_2(p_2,\gamma)$，同理 $\mathcal{W}(\mathcal{R})=1$。
  - 由凸性，中间分布均可精确匹配。
- **结论**：$a_1 = \alpha$ 可成功防御 $a_2 = \gamma$。

#### 检查 $(p_1, p_2)$，$a_2 = \delta$

- 尝试 $a_1 = \alpha$：
  - $\mathcal{P}_1(p_1,\alpha) \subseteq \mathcal{P}_2(p_2,\delta)$？
    - $\mathcal{P}_1(p_1,\alpha)$：$q_1 \in [0.1, 0.6]$。
    - $\mathcal{P}_2(p_2,\delta)$：$q_2 \in [0.1, 0.8]$。
    - 显然 $[0.1, 0.6] \subseteq [0.1, 0.8]$，且归一化后 $r_1 = 1-q_1$ 自动满足 $r_2$ 的区间。
  - 因此对任意 $\mu_1 \in \mathcal{P}_1(p_1,\alpha)$，取 $\mu_2 = \mu_1 \in \mathcal{P}_2(p_2,\delta)$ 即可精确匹配。
- **结论**：$a_1 = \alpha$ 可成功防御 $a_2 = \delta$。

#### 结论（Competitive $\varepsilon=0$）

$(p_1,p_2)$ 满足 competitive 精确模拟条件。结合 $(q_1,q_2)$、$(r_1,r_2)$ 的自环显然成立，最大关系为：
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

### 3.3 Competitive 语义，$\varepsilon = 0.5$（$t=0.5$）

此时 $\mathcal{P}_2(p_2,\gamma)$ 扩大为 $q_2 \in [0.1, 1.0]$。

#### 检查 $(p_1, p_2)$，$a_2 = \gamma$

- 尝试 $a_1 = \alpha$：
  - $\mu_1 = (0.1, 0.9)$：取 $\mu_2 = (0.1, 0.9) \in \mathcal{P}_2(p_2,\gamma)$（因 $q_2=0.1$ 为下界，$r_2=0.9 \in [0,0.9]$）。$\mathcal{W}(\mathcal{R}) = 1 \geq 0.5$。
  - $\mu_1 = (0.6, 0.4)$：取 $\mu_2 = (0.6, 0.4) \in \mathcal{P}_2(p_2,\gamma)$（因 $q_2=0.6 \leq 1.0$，$r_2=0.4 \geq 0$）。$\mathcal{W}(\mathcal{R}) = 1 \geq 0.5$。
- **结论**：$a_1 = \alpha$ 可防御 $a_2 = \gamma$。

#### 检查 $(p_1, p_2)$，$a_2 = \delta$

- 尝试 $a_1 = \beta$：
  - $\mu_1 = (0.0, 1.0)$（corner）：
    - 需构造 $\mu_2 \in \mathcal{P}_2(p_2,\delta)$ 使得耦合 $\mathcal{W}(\mathcal{R}) \geq 0.5$。
    - 由于 $\mu_1(q_1)=0$，耦合中 $\mathcal{W}(q_1,\cdot)=0$，故 $\mathcal{W}(\mathcal{R}) = \mathcal{W}(r_1,r_2) = \mu_2(r_2)$。
    - 需 $\mu_2(r_2) \geq 0.5$，即 $\mu_2(q_2) \leq 0.5$。
    - $\mathcal{P}_2(p_2,\delta)$ 允许 $q_2 \in [0.1, 0.8]$，取 $\mu_2 = (0.2,\, 0.8)$。
    - 耦合：$\mathcal{W}(r_1,q_2)=0.2$，$\mathcal{W}(r_1,r_2)=0.8$，$\mathcal{W}(\mathcal{R}) = 0.8 \geq 0.5$。
  - $\mu_1 = (0.6, 0.4)$（corner）：
    - 取 $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\delta)$（$q_2=0.6 \in [0.1,0.8]$，$r_2=0.4 \in [0.2,0.9]$）。
    - 耦合：$\mathcal{W}(q_1,q_2)=0.6$，$\mathcal{W}(r_1,r_2)=0.4$，$\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$。
  - 由凸性，中间分布均可匹配。
- **结论**：$a_1 = \beta$ 可防御 $a_2 = \delta$。

#### 结论（Competitive $\varepsilon=0.5$）

$$\mathcal{M}_2 \preceq_{0.5}^{\forall\exists} \mathcal{M}_1$$
最大关系仍为 $\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$。

---

## 4. Running Example 2：Algorithm 1（Cooperative，$\varepsilon = 0.2$）

**设定**：$t = 0.2$（对应 $\varepsilon=0.2$），此时
- $\mathcal{P}_2(p_2,\gamma) = \{(q,1-q) \mid q \in [0.1, 0.8]\}$（上界 $0.6+0.2=0.8$）
- $\mathcal{P}_2(p_2,\delta) = \{(q,1-q) \mid q \in [0.1, 0.8]\}$（与 $\gamma$ 恰好相同）

**初始化**：
$$\mathcal{R} \leftarrow \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

### Iteration 1

检查 $(p_1, p_2)$：

**（a）$a_1 = \alpha$，corners of $\mathcal{P}_1(p_1,\alpha)$：**

- Corner $c_{1,\alpha}^{(1)} = (0.1,\, 0.9)$：
  - 尝试 $a_2 = \gamma$：取 $\mu_2 = (0.1,\, 0.9) \in \mathcal{P}_2(p_2,\gamma)$。
  - 耦合：$\mathcal{W}(q_1,q_2)=0.1$，$\mathcal{W}(r_1,r_2)=0.9$。
  - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$。**可行**。

- Corner $c_{1,\alpha}^{(2)} = (0.6,\, 0.4)$：
  - 尝试 $a_2 = \gamma$：取 $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\gamma)$。
  - 耦合：$\mathcal{W}(q_1,q_2)=0.6$，$\mathcal{W}(r_1,r_2)=0.4$。
  - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$。**可行**。

**（b）$a_1 = \beta$，corners of $\mathcal{P}_1(p_1,\beta)$：**

- Corner $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$：
  - 尝试 $a_2 = \delta$：需 $\mathcal{W}(\mathcal{R}) \geq 0.8$。
  - 由于 $\mu_1(q_1)=0$，$\mathcal{W}(\mathcal{R}) = \mu_2(r_2)$，需 $\mu_2(r_2) \geq 0.8$（即 $\mu_2(q_2) \leq 0.2$）。
  - $\mathcal{P}_2(p_2,\delta)$ 允许 $q_2 \in [0.1, 0.8]$，取 $\mu_2 = (0.2,\, 0.8)$。
  - 耦合：$\mathcal{W}(r_1,q_2)=0.2$，$\mathcal{W}(r_1,r_2)=0.8$。
  - $\mathcal{W}(\mathcal{R}) = 0.8 \geq 0.8$。**可行**。

- Corner $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$：
  - 尝试 $a_2 = \delta$：取 $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\delta)$。
  - 耦合：$\mathcal{W}(q_1,q_2)=0.6$，$\mathcal{W}(r_1,r_2)=0.4$。
  - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.8$。**可行**。

检查 $(q_1, q_2)$ 与 $(r_1, r_2)$：自环 trivial，保留。

**本轮移除**：无。

### Iteration 2
$\mathcal{R}$ 未变化，算法终止。

**输出**：
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

## 5. Running Example 3：Algorithm 2（Competitive，$\varepsilon = 0.5$）

**设定**：$t = 0.5$，此时
- $\mathcal{P}_2(p_2,\gamma) = \{(q,1-q) \mid q \in [0.1, 1.0]\}$
- $\mathcal{P}_2(p_2,\delta) = \{(q,1-q) \mid q \in [0.1, 0.8]\}$

**初始化**：
$$\mathcal{R} \leftarrow \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

### Iteration 1

检查 $(p_1, p_2)$：

**（a）$a_2 = \gamma$：**

- 尝试 $a_1 = \alpha$：
  - Corner $c_{1,\alpha}^{(1)} = (0.1,\, 0.9)$：
    - 取 $\mu_2 = (0.1,\, 0.9) \in \mathcal{P}_2(p_2,\gamma)$。
    - 耦合：$\mathcal{W}(q_1,q_2)=0.1$，$\mathcal{W}(r_1,r_2)=0.9$。
    - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$。**可行**。
  - Corner $c_{1,\alpha}^{(2)} = (0.6,\, 0.4)$：
    - 取 $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\gamma)$。
    - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$。**可行**。
  - 所有 corners 可行，设置 $found \leftarrow \text{True}$。

**（b）$a_2 = \delta$：**

- 尝试 $a_1 = \beta$：
  - Corner $c_{1,\beta}^{(1)} = (0.0,\, 1.0)$：
    - 需 $\mathcal{W}(\mathcal{R}) \geq 0.5$。由于 $\mu_1(q_1)=0$，$\mathcal{W}(\mathcal{R}) = \mu_2(r_2)$。
    - 取 $\mu_2 = (0.2,\, 0.8) \in \mathcal{P}_2(p_2,\delta)$，则 $\mathcal{W}(\mathcal{R}) = 0.8 \geq 0.5$。**可行**。
  - Corner $c_{1,\beta}^{(2)} = (0.6,\, 0.4)$：
    - 取 $\mu_2 = (0.6,\, 0.4) \in \mathcal{P}_2(p_2,\delta)$。
    - $\mathcal{W}(\mathcal{R}) = 1.0 \geq 0.5$。**可行**。
  - 所有 corners 可行，设置 $found \leftarrow \text{True}$。

检查 $(q_1, q_2)$、$(r_1, r_2)$：自环 trivial。

**本轮移除**：无。

### Iteration 2
$\mathcal{R}$ 未变化，算法终止。

**输出**：
$$\mathcal{R} = \{(p_1,p_2),\, (q_1,q_2),\, (r_1,r_2)\}$$

---

## 6. 程序复现提示

### 6.1 数据结构定义

```python
# M1
X1 = ['p1', 'q1', 'r1']
A1 = ['alpha', 'beta']
x0_1 = 'p1'
# P1_lower[x][a][x_next], P1_upper[x][a][x_next]
# 示例：P1_lower['p1']['alpha']['q1'] = 0.1

# M2
X2 = ['p2', 'q2', 'r2']
A2 = ['gamma', 'delta']
x0_2 = 'p2'

# 候选关系
R = {('p1','p2'), ('q1','q2'), ('r1','r2')}

## 6.2 Feasible Set Corners 生成

对每个 $(x,a)$，先由区间与归一化约束解析出各后继状态概率的显式可行区间，再取极值点。对于仅有两个后继状态的情况（如 $p_1$ 的动作），可直接参数化 $p(q)=t$，$p(r)=1-t$，求出 $t$ 的闭区间，端点即为 corners。

## 6.3 Coupling LP（Definition 6）

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

## 6.4 关键核对点

建议程序复现时优先验证以下手动推导结论：

1. **Cooperative $\varepsilon=0$**：$(p_1,p_2)$ 应被移除，因为 $a_1=\beta$ 的 corner $(0,1)$ 无法被任何 $a_2$ 精确匹配。
2. **Competitive $\varepsilon=0$**：$(p_1,p_2)$ 应保留，因为 $a_2=\gamma$ 可由 $a_1=\alpha$ 精确防御，$a_2=\delta$ 也可由 $a_1=\alpha$ 精确防御。
3. **Algorithm 1 ($\varepsilon=0.2$）**：$(p_1,p_2)$ 保留，$a_1=\beta$ 的 corner $(0,1)$ 对 $a_2=\delta$ 取 $\mu_2=(0.2,0.8)$ 刚好满足 $\mathcal{W}(\mathcal{R})=0.8$。
4. **Algorithm 2 ($\varepsilon=0.5$）**：$(p_1,p_2)$ 保留，$a_2=\delta$ 由 $a_1=\beta$ 防御时，corner $(0,1)$ 取 $\mu_2=(0.2,0.8)$ 满足 $\mathcal{W}(\mathcal{R})=0.8 \geq 0.5$。

## 附录：Coupling LP 显式示例

以 Example 2 中 $(p_1,\beta)$ vs $(p_2,\delta)$、corner $c_1=(0,1)$、$\varepsilon=0.2$ 为例：

**已知**：
- $c_1(q_1)=0,\; c_1(r_1)=1$
- $C(p_2,\delta) = \{(0.1,0.9),\, (0.8,0.2)\}$

**变量**：$\mathcal{W}_{qq}, \mathcal{W}_{qr}, \mathcal{W}_{rq}, \mathcal{W}_{rr}, \beta_1, \beta_2$

**约束**：

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

**可行解**：取 $\beta_1=1, \beta_2=0$（即 $\mu_2=(0.1,0.9)$），则
- $\mathcal{W}_{rq}=0.1,\; \mathcal{W}_{rr}=0.9$，其余为 0。
- $\mathcal{W}(\mathcal{R})=0.9 \geq 0.8$。

或取 $\mu_2=(0.2,0.8)$（非 corner，但可由 corners 凸组合得到），则
- $\mathcal{W}_{rq}=0.2,\; \mathcal{W}_{rr}=0.8$。
- $\mathcal{W}(\mathcal{R})=0.8 \geq 0.8$。
