# Experiment Record — IMDP Approximate Simulation Verification

## Environment

| Item | Value |
|------|-----|
| Date | 2026-07-05 |
| Case | new_model.md (colleague-designed) |
| Python | 3.12.7 (dyabstract conda env) |
| LP Solver | HIGHS |
| Git commit | fe4c5ff + lazy_enum/algorithm fixes |

---

## Experiment 1: Build IMDP + Data Structure Verification ✓

### Purpose
Verify that the P_full / S_id data structures for M1 and M2 are correct, and that feasible sets and corners match the documentation.

### Expected
- M1(p1,α): corners = [(0.4, 0.6), (0.7, 0.3)]
- M1(p1,β): corners = [(0.2, 0.8), (0.6, 0.4)]
- M2(p2,γ): corners = [(0.2, 0.8), (0.8, 0.2)]
- M2(p2,δ): corners = [(0.2, 0.8), (0.4, 0.6)]

### Result

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

**Conclusion**: All 4 feasible set corners match the analytical derivations in the documentation exactly. ✓

---

## Experiment 2: Direct Coupling Check — Lazy Method ✓

### Purpose
Directly call check_coupling_lazy to verify coupling feasibility for each (s1,s2) pair at different ε values.

### Expected

| Pair | ε=0 | ε=0.2 | Bottleneck |
|------|-----|-------|------|
| (p1,p2) | ✗ (a2=δ, a1=β corner (0.6,0.4) fails) | ✓ (W(R)=0.8) | P(p2,δ)=[0.2,0.4] too narrow |
| (q1,q2) | ✓ | ✓ | Self-loop trivial |
| (r1,r2) | ✓ | ✓ | Self-loop trivial |

### Result

```
  ε = 0.0:
    ✗ (p1,p2): FAILED a2=[1]    ← a2=δ cannot be defended, consistent with doc Section 3.2
    ✓ (q1,q2)
    ✓ (r1,r2)

  ε = 0.2:
    ✓ (p1,p2)                    ← a1=β successfully defends a2=δ, W(R)=0.8
    ✓ (q1,q2)
    ✓ (r1,r2)
```

**Conclusion**:
- ε=0: (p1,p2) fails on a2=δ (corner (0.6,0.4) cannot exactly match the narrow interval [0.2,0.4])
- ε=0.2: a1=β successfully defends a2=δ (corner (0.6,0.4) coupling exactly 0.8 = 1-ε)
- Fully consistent with the analytical derivations in doc Sections 3.2 and 5. ✓

---

## Experiment 3: Full Pipeline — ε_min Binary Search ✓

### Purpose
Run compute_min_epsilon to verify ε_min ≈ 0.2.

### Expected
- ε_min(lazy) ≈ ε_min(corner) ≈ 0.2
- ε=1.0: feasible, |R|=3
- ε=0.0: infeasible, |R|=2 ((p1,p2) removed)
- binary search converges to ε_min ≈ 0.2

### Corner Results

```
  ε_min      = 0.200012
  |R_final|  = 3
  LP calls   = 82
  Wall time  = 0.73s
```

Binary search process:
```
  ε=1.000000  feasible= True   |R|= 3   ← starting point
  ε=0.000000  feasible=False   |R|= 2   ← (p1,p2) removed
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

**Key observations**:
- ε=0.199951: infeasible. ε=0.200012: feasible.
- The threshold lies between 0.199951~0.200012, closely matching the theoretical value 0.2 (error < 1e-4).
- When ε ≥ 0.2, (p1,p2) survives (|R|=3); when ε < 0.2, (p1,p2) is removed (|R|=2).

### Lazy Results

```
  ε_min      = 0.200012
  |R_final|  = 3
  LP calls   = 75
  Wall time  = 0.55s
```

---

## Experiment 4: Lazy vs Corner Cross-Validation ✓

### Results

| Metric | Corner | Lazy | Match |
|------|--------|------|-------|
| ε_min | 0.200012 | 0.200012 | ✓ |
| \|R\| | 3 | 3 | ✓ |
| LP calls | 82 | 75 | Lazy 8.5% fewer |

### LP Call Analysis

Corner method: each (state, action) enumerates all 2 corners, each corner calls LP once.
Lazy method: uses cutting-plane to generate corners on demand. In this case, when k1=2 the corner count is the same, but lazy skips extra LPs when k1=1 (self-loop states).

---

## Summary

| Check Item | Status |
|--------|------|
| Corners match documentation | ✓ |
| (p1,p2) removed at ε=0 | ✓ |
| (p1,p2) survives at ε=0.2 | ✓ |
| ε_min ≈ 0.2 (analytical prediction) | ✓ (0.200012) |
| Lazy = Corner (ε_min and R consistent) | ✓ |
| No lazy convergence warnings | ✓ |
| a2=δ must be defended by a1=β (not α) | ✓ (verified in Experiment 2) |
| Corner (0.6,0.4) coupling = 0.8 exactly = 1-ε | ✓ (knife-edge numerical precision OK) |
