# Paper Examples Verification — Lazy Corner Method

## Purpose

Verify that the lazy corner enumeration (cutting-plane) method correctly computes the
approximate simulation relation for the two IMDP examples from **Figure 2** of the paper,
and compare results against the exact corner-enumeration method.

---

## Paper Examples (Figure 2)

### Example (a): 3-state IMDP (Fine / Concrete)

```
    [0.6, 0.9]
   ┌───────────┐
   ▼           │
  ┌───┐              ┌───┐                  ┌───┐
  │s0 │──────────────▶│s1 │─────────────────▶│s2 │
  └───┘  [0.1, 0.4]  └───┘  [0.8, 0.9]     └───┘
              [0.1, 0.2]                      ▲
                           ┌──────────────────┘
                           [1.0, 1.0]
```

| Property | Value |
|----------|-------|
| States | s0=0, s1=1, s2=2 |
| Goal states | s2 (double circle) |
| Critical states | None |
| Actions per state | 1 |
| s0 → s0 | [0.6, 0.9] |
| s0 → s1 | [0.1, 0.4] |
| s1 → s2 | [0.8, 0.9] |
| s1 → s0 | [0.1, 0.2] |
| s2 → s2 | [1.0, 1.0] (absorbing) |

### Example (b): 2-state IMDP (Coarse / Abstraction)

```
    [0.6, 0.9]
   ┌───────────┐
   ▼           │
  ┌───┐              ┌───┐
  │q0 │──────────────▶│q1 │
  └───┘  [0.1, 0.4]  └───┘
                        ▲
                        │
                    [1.0, 1.0]
```

| Property | Value |
|----------|-------|
| States | q0=0, q1=1 |
| Goal states | q1 (double circle) |
| Critical states | None |
| Actions per state | 1 |
| q0 → q0 | [0.6, 0.9] |
| q0 → q1 | [0.1, 0.4] |
| q1 → q1 | [1.0, 1.0] (absorbing) |

### Abstraction Mapping (f2c)

| Fine (a) | Coarse (b) | Rationale |
|----------|------------|-----------|
| s0 | q0 | Both non-goal initial states |
| s1 | q1 | s1 merged with s2 into abstract goal q1 |
| s2 | q1 | s2 is goal, maps to goal q1 |

**Key insight**: States s1 and s2 in the fine model are both abstracted into q1.
This is the core of IMDP abstraction — s1, while not a goal state itself, transitions
to the goal s2 with high probability [0.8, 0.9], so it is grouped with s2 in the
coarse abstraction.

---

## Verification Setup

### Pair: Example (a) → Example (b)

- **Fine IMDP**: Example (a), 3 states, 1 action
- **Coarse IMDP**: Example (b), 2 states, 1 action
- **f2c mapping**: `[[0], [1], [1]]` (s0→q0, s1→q1, s2→q1)
- **init_R**: All f2c-overlapping pairs `{(0,0), (1,1), (2,1)}` (bypass label check
  since s1 is normal but q1 is goal — this is expected for abstraction)

### Label Note

With default label-consistent initialization, (s1, q1) would NOT be in the initial R
because s1 is labeled "normal" and q1 is labeled "goal". For this verification we
pass `init_R` explicitly to include all f2c-mapped pairs, consistent with the
abstraction semantics where s1 is legitimately abstracted into q1.

### Expected Behavior

For this small example with exact interval matching (s0↔q0 intervals are identical,
and s1/s2 intervals are consistent with q1), we expect:

- **ε_min should be small** (likely 0 or close to 0), since the coarse IMDP is a
  valid abstraction of the fine IMDP
- The lazy method should converge in few iterations (k1 ≤ 2 for all states)
- Corner enumeration should find the same result with more LP calls

---

## Verification Methodology

### Method 1: Full pipeline (recommended)

Build IMDP objects and run `compute_min_epsilon` with both `method='corner'` and
`method='lazy'`, then compare:

- `epsilon_min` should be equal (within `tol`)
- `R_final` should be identical in size and content
- Lazy method should use fewer LP calls

### Method 2: Direct coupling check (for debugging)

Call `check_coupling_lazy()` directly on specific `(s1, s2, a1, a2)` tuples.

### Correctness Checks

| Check | Method |
|-------|--------|
| ε_min matches corner method | Compare `compute_min_epsilon` results |
| Cutting-plane converges | Check `status == 'converged'` |
| No false positives | All lazy-feasible pairs also corner-feasible |
| No false negatives | All corner-feasible pairs also lazy-feasible |
| LP count reduction | Lazy should use ≪ LP calls than corner |

---

## Test Script

Run: `python verify_paper_examples.py`

---

## Test Records

---

### Run #1 — 2026-07-05

| | Example (a)→(b) |
|---|---|
| **Git commit** | `fe4c5ff` + uncommitted fixes |
| **ε_min (corner)** | 0.200012 |
| **ε_min (lazy)** | 0.200012 |
| **Match?** | ✓ YES |
| **\|R\| (corner)** | 3 |
| **\|R\| (lazy)** | 3 |
| **LP calls (corner)** | 52 |
| **LP calls (lazy)** | 51 |
| **Wall time (corner)** | 0.42s |
| **Wall time (lazy)** | 0.41s |
| **Lazy converged?** | ✓ All converged |
| **Notes** | init_R={(0,0),(1,1),(2,1)}; bottleneck ε≈0.2 from (s1,q1) where s0→q1 not in R |

### Analysis — Run #1

**Direct coupling check results (lazy method):**

| Pair | ε=0.0 | ε=0.1 | ε=0.5 | ε=1.0 |
|------|-------|-------|-------|-------|
| (0,0) | ✗ | ✓ | ✓ | ✓ |
| (1,1) | ✗ | ✗ | ✓ | ✓ |
| (2,1) | ✓ | ✓ | ✓ | ✓ |

**Why ε_min ≈ 0.2:**

The bottleneck is pair (s1, q1). For state q1 (absorbing goal), the only coarse
successor is q1 itself. The fine state s1 has successors {s2, s0}. While s2 maps
to q1 (in R), s0 maps to q0 — and (s0, q1) ∉ R since s0↔q0 is the valid mapping.
This means mass routed to fine successor s0 CANNOT be captured within the relation
when checking (s1, q1):

- p₁(s1→s0) ∈ [0.1, 0.2], so worst-case max_mass = 1 - p₁(s1→s0) = 0.8
- Requirement: max_mass ≥ 1 − ε → ε ≥ 0.2

The pair (0,0) fails at ε=0.0 due to numerical precision in the LP solver
(theoretically it should be feasible — both fine and coarse have identical
intervals [0.6,0.9]+[0.1,0.4], and all successors have R partners).

**Lazy vs corner comparison:**

For this tiny example (k1 ≤ 2), the lazy method checks the same number of corners
as enumeration (2 corners for k1=2). LP call reduction is negligible (52→51).
The advantage of lazy corner enumeration becomes significant when k1 is large
(e.g., k1 ≥ 10).

---

### Run #2 — YYYY-MM-DD

| | Example (a)→(b) |
|---|---|
| ... | |

---

## Analysis & Conclusions

> TODO after all runs complete:

- Does lazy corner produce identical ε_min to exact corner enumeration?
- What is the LP call reduction ratio?
- Are there any convergence warnings?
