"""k1 = 3 sub-example: makes the lower bound's subset-minimization visible.

The running example (M1/M2) has k1 = 2 everywhere, so the bound's core
operation -- min over subsets A subseteq U, with the neighborhood N(A) -- is
trivial (4 subsets).  This constructed fragment uses k1 = k2 = 3 so that:

  - |C(P1)| = 4+ corners, |A subseteq U| = 8 subsets,
  - N(A) has non-trivial structure (not just a diagonal),
  - the per-subset table A | N(A) | L1(A) | U2(N(A)) | L2(N(A)) | summands
    shows exactly what UB and LB_min are minimizing over.

It is a single (s1,a1,s2,a2) coupling check, not part of M1/M2 -- a
pedagogical add-on to exhibit the combinatorics the running example hides.
"""
import itertools
import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=' ')


# ---- box-simplex primitives (general k) ----
def corners(lb, ub):
    k = len(lb)
    uniq = []
    for piv in range(k):
        for m in itertools.product([0, 1], repeat=k):
            base = np.array([lb[i] if m[i] == 0 else ub[i] for i in range(k)], float)
            rem = 1.0 - base.sum()
            base[piv] += rem
            if (np.all(base >= lb - 1e-9) and np.all(base <= ub + 1e-9)
                    and abs(base.sum() - 1) < 1e-9):
                p = np.clip(base, lb, ub)
                if not any(np.allclose(p, q) for q in uniq):
                    uniq.append(p)
    return uniq


def L1(A, lb, ub):
    U = range(len(lb))
    S = [i for i in U if i not in A]
    return max(sum(lb[i] for i in S), 1.0 - sum(ub[i] for i in A))


def U2(S, lb, ub):
    U = range(len(lb))
    ns = [i for i in U if i not in S]
    return min(sum(ub[i] for i in S), 1.0 - sum(lb[i] for i in ns))


def L2(S, lb, ub):
    U = range(len(lb))
    ns = [i for i in U if i not in S]
    return max(sum(lb[i] for i in S), 1.0 - sum(ub[i] for i in ns))


def Phi(c, q, R, k):
    U = range(k)
    subs = (s for r in range(k + 1) for s in itertools.combinations(U, r))
    best = np.inf
    for A in subs:
        NA = {j for i in A for (ii, j) in R if ii == i}
        val = c.sum() - c[list(A)].sum() + sum(q[j] for j in NA)
        best = min(best, val)
    return best


def M_c(c, lb2, ub2, R, k):
    """M(c) = max_{q in P2} max_W W(R) via LP (interior optimum possible)."""
    import cvxpy as cp
    W = cp.Variable((k, k))
    q = cp.Variable(k)
    cons = [W >= 0, lb2 <= q, q <= ub2, cp.sum(q) == 1,
            cp.sum(W, axis=1) == c, cp.sum(W, axis=0) == q]
    rp = [W[i, j] for (i, j) in R]
    obj = cp.Maximize(rp[0] if len(rp) == 1 else cp.sum(cp.hstack(rp)))
    cp.Problem(obj, cons).solve()
    # also recover the optimal q*
    return float(obj.value), np.round(q.value, 6)


def LBstar_lp(lb1, ub1, lb2, ub2, R, k):
    """LB* = max_{q* in P2} min_A [L1(A)+q*(N(A))] as an LP; returns (val, q*)."""
    import cvxpy as cp
    U = range(k)
    subs = [s for r in range(k + 1) for s in itertools.combinations(U, r)]
    q = cp.Variable(k)
    t = cp.Variable()
    cons = [lb2 <= q, q <= ub2, cp.sum(q) == 1]
    for A in subs:
        NA = sorted({j for i in A for (ii, j) in R if ii == i})
        term = L1(list(A), lb1, ub1) + (cp.sum(q[NA]) if NA else 0)
        cons.append(t <= term)
    cp.Problem(cp.Maximize(t), cons).solve()
    return float(t.value), np.round(q.value, 6)


# ---------------------------------------------------------------------------
# Constructed k1=3 fragment
# ---------------------------------------------------------------------------
# Fine successors  U = {0,1,2}; coarse successors V = {0,1,2}.
# R with non-trivial neighborhood: 0->{0,1}, 1->{1}, 2->{2}
R = [(0, 0), (0, 1), (1, 1), (2, 2)]
k = 3

# Nonzero lowers on both sides (exercises the general Lemma-2 forms).
lb1 = np.array([0.1, 0.0, 0.2]);  ub1 = np.array([0.5, 0.6, 0.7])   # sum lb=.3, sum ub=1.8
lb2 = np.array([0.0, 0.1, 0.0]);  ub2 = np.array([0.5, 0.7, 0.6])   # sum lb=.1, sum ub=1.8

Cf = corners(lb1, ub1)
print("Fine P1: lb =", lb1, " ub =", ub1)
print("Fine corners C(P1) =", [c.tolist() for c in Cf], f"  ({len(Cf)} vertices)")
print("Coarse P2: lb =", lb2, " ub =", ub2)
print("R =", R, "  (neighborhood: N({0})={0,1}, N({1})={1}, N({2})={2})\n")

U = range(k)
subs = [s for r in range(k + 1) for s in itertools.combinations(U, r)]


def N(A):
    return sorted({j for i in A for (ii, j) in R if ii == i})


# ---- per-subset table: what UB and LB_min minimize over ----
print("Per-subset table (the object the bounds minimize over A subseteq U):")
print(f"  {'A':<10}{'N(A)':<12}{'L1(A)':>8}{'U2(N(A))':>10}{'L2(N(A))':>10}"
      f"{'L1+U2 (UB-term)':>18}{'L1+L2 (LBmin-term)':>20}")
ub_rows, lbmin_rows = [], []
for A in subs:
    NA = N(A)
    l1 = L1(list(A), lb1, ub1)
    u2 = U2(NA, lb2, ub2)
    l2 = L2(NA, lb2, ub2)
    ub_rows.append(l1 + u2)
    lbmin_rows.append(l1 + l2)
    Astr = str(set(A)) if A else "{}"
    print(f"  {Astr:<10}{str(set(NA)):<12}{l1:>8.4f}{u2:>10.4f}{l2:>10.4f}"
          f"{l1+u2:>18.4f}{l1+l2:>20.4f}")
UB = min(ub_rows)
LBmin = min(lbmin_rows)
print(f"\n  UB     = min_A [L1+U2(N(A))] = {UB:.4f}")
print(f"  LB_min = min_A [L1+L2(N(A))] = {LBmin:.4f}")

# ---- exact g and the per-corner optimal coarse q* (to exhibit disjunction) ----
print("\nPer fine corner: M(c) and its optimal coarse marginal q*_c")
Mvals, qstars = [], []
for c in Cf:
    mc, qc = M_c(c, lb2, ub2, R, k)
    Mvals.append(mc)
    qstars.append(qc)
    print(f"  c={np.round(c,4).tolist()}  M(c)={mc:.4f}  optimal q*_c={qc.tolist()}")
g = min(Mvals)
print(f"\n  g = min_c M(c) = {g:.4f}")

# ---- LB* via LP ----
LBstar, qstar_lb = LBstar_lp(lb1, ub1, lb2, ub2, R, k)
print(f"  LB*   = max_{{q* in P2}} min_A [L1(A)+q*(N(A))] = {LBstar:.4f}  "
      f"(at q*={qstar_lb.tolist()})")

# ---- bracket check ----
TOL = 1e-6
ok = (LBmin <= LBstar + TOL and LBstar <= g + TOL and g <= UB + TOL)
print(f"\n  bracket: LB_min={LBmin:.4f} <= LB*={LBstar:.4f} <= g={g:.4f} <= UB={UB:.4f}"
      f"   -> {'OK' if ok else 'FAIL'}")
print(f"  gap (UB - LB*) = {UB-LBstar:.4f}   (disjunction; >0 if optimal q* is "
      f"corner-dependent)")

# disjunction check: do the per-corner optimal q*_c differ?
distinct = not all(np.allclose(qstars[0], q, atol=1e-3) for q in qstars[1:])
print(f"  per-corner optimal q*_c differ across corners? {distinct} "
      f"(True <=> gap expected)")
