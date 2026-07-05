# 实验记录 — IMDP 近似模拟验证

## 环境

| 项目 | 值 |
|------|-----|
| 日期 | 2026-07-05 |
| 案例 | new_model.md（同事设计） |
| Python | 3.12.7 (dyabstract conda env) |
| LP Solver | HIGHS |
| Git commit | fe4c5ff + lazy_enum/algorithm fixes |

---

## 实验 1: 构建 IMDP + 数据结构验证 ✓

### 目的
验证 M1 和 M2 的 P_full / S_id 数据结构正确，feasible set 和 corners 与文档一致。

### 预期
- M1(p1,α): corners = [(0.4, 0.6), (0.7, 0.3)]
- M1(p1,β): corners = [(0.2, 0.8), (0.6, 0.4)]
- M2(p2,γ): corners = [(0.2, 0.8), (0.8, 0.2)]
- M2(p2,δ): corners = [(0.2, 0.8), (0.4, 0.6)]

### 结果

```
  ✓ M1 (p1,α): succ=[1, 2], pl=[0.2, 0.1], pu=[0.7, 0.6]
     corners=[(0.4, 0.6), (0.7, 0.3)]
  ✓ M1 (p1,β): succ=[1, 2], pl=[0.1, 0.2], pu=[0.6, 0.8]
     corners=[(0.2, 0.8), (0.6, 0.4)]
  ✓ M2 (p2,γ): succ=[1, 2], pl=[0.1, 0.1], pu=[0.8, 0.8]
     corners=[(0.2, 0.8), (0.8, 0.2)]
  ✓ M2 (p2,δ): succ=[1, 2], pl=[0.1, 0.4], pu=[0.4, 0.8]
     corners=[(0.2, 0.8), (0.4, 0.6)]
  ALL PASS
```

**结论**: 所有 4 个 feasible set 的 corners 与文档解析推导完全一致。✓

---

## 实验 2: Direct Coupling Check — Lazy 方法 ✓

### 目的
直接调用 check_coupling_lazy，验证各 (s1,s2) 对在不同 ε 下的耦合可行性。

### 预期

| Pair | ε=0 | ε=0.2 | 瓶颈 |
|------|-----|-------|------|
| (p1,p2) | ✗ (a2=δ, a1=β corner (0.6,0.4) fails) | ✓ (W(R)=0.8) | P(p2,δ)=[0.2,0.4] 太窄 |
| (q1,q2) | ✓ | ✓ | 自环 trivial |
| (r1,r2) | ✓ | ✓ | 自环 trivial |

### 结果

```
  ε = 0.0:
    ✗ (p1,p2): FAILED a2=[1]    ← a2=δ 无法防御，与文档 Section 3.2 一致
    ✓ (q1,q2)
    ✓ (r1,r2)

  ε = 0.2:
    ✓ (p1,p2)                    ← a1=β 成功防御 a2=δ，W(R)=0.8
    ✓ (q1,q2)
    ✓ (r1,r2)
```

**结论**: 
- ε=0: (p1,p2) 在 a2=δ 时失败（corner (0.6,0.4) 无法精确匹配窄区间 [0.2,0.4]）
- ε=0.2: a1=β 防御 a2=δ 成功（corner (0.6,0.4) 耦合恰好 0.8 = 1-ε）
- 与文档 Section 3.2 和 5 的解析推导完全一致。✓

---

## 实验 3: Full Pipeline — ε_min Binary Search ✓

### 目的
运行 compute_min_epsilon，验证 ε_min ≈ 0.2。

### 预期
- ε_min(lazy) ≈ ε_min(corner) ≈ 0.2
- ε=1.0: feasible, |R|=3
- ε=0.0: infeasible, |R|=2（(p1,p2) 移除）
- binary search 收敛到 ε_min ≈ 0.2

### Corridor 结果

```
  ε_min      = 0.200012
  |R_final|  = 3
  LP calls   = 82
  Wall time  = 0.73s
```

Binary search 过程：
```
  ε=1.000000  feasible= True   |R|= 3   ← 起点
  ε=0.000000  feasible=False   |R|= 2   ← (p1,p2) 移除
  ε=0.500000  feasible= True   |R|= 3   
  ε=0.250000  feasible= True   |R|= 3   
  ε=0.125000  feasible=False   |R|= 2   
  ε=0.187500  feasible=False   |R|= 2   
  ε=0.218750  feasible= True   |R|= 3   
  ε=0.203125  feasible= True   |R|= 3   
  ε=0.195312  feasible=False   |R|= 2   
  ε=0.199219  feasible=False   |R|= 2   
  ε=0.201172  feasible= True   |R|= 3   
  ε=0.200195  feasible= True   |R|= 3   
  ε=0.199707  feasible=False   |R|= 2   
  ε=0.199951  feasible=False   |R|= 2   
  ε=0.200073  feasible= True   |R|= 3   
  ε=0.200012  feasible= True   |R|= 3   
```

**关键观察**：
- ε=0.199951: infeasible。ε=0.200012: feasible。
- 阈值在 0.199951~0.200012 之间，与理论值 0.2 高度吻合（误差 < 1e-4）。
- ε ≥ 0.2 时 (p1,p2) 存活（|R|=3），ε < 0.2 时 (p1,p2) 移除（|R|=2）。

### Lazy 结果

```
  ε_min      = 0.200012
  |R_final|  = 3
  LP calls   = 75
  Wall time  = 0.55s
```

---

## 实验 4: Lazy vs Corner 交叉验证 ✓

### 结果

| 指标 | Corner | Lazy | Match |
|------|--------|------|-------|
| ε_min | 0.200012 | 0.200012 | ✓ |
| \|R\| | 3 | 3 | ✓ |
| LP calls | 82 | 75 | Lazy 少 8.5% |

### LP call 分析

Corner 方法：每个 (state, action) 枚举所有 2 个 corner，每个 corner 调用 1 次 LP。
Lazy 方法：用 cutting-plane 按需生成 corner，在此例中 k1=2 时 corner 数相同，
但 lazy 在 k1=1（自环状态）时跳过额外的 LP。

---

## 总结

| 检查项 | 状态 |
|--------|------|
| Corners 与文档一致 | ✓ |
| ε=0 时 (p1,p2) 被移除 | ✓ |
| ε=0.2 时 (p1,p2) 存活 | ✓ |
| ε_min ≈ 0.2（解析预测） | ✓ (0.200012) |
| Lazy = Corner（ε_min 和 R 一致） | ✓ |
| 无 lazy 收敛警告 | ✓ |
| a2=δ 必须由 a1=β（非 α）防御 | ✓（实验 2 验证） |
| Corner (0.6,0.4) 耦合 = 0.8 恰好 = 1-ε | ✓（knife-edge 数值精度 OK） |
